#!/usr/bin/env python3
"""Small 2-layer grid router (A*, 45-degree moves, vias) for this board.

Reads  build/geometry.json  (tools/gen_pcb.py geom)
Writes build/routes.json    (consumed by tools/gen_pcb.py finish)

Clearance model: every copper item is rasterised on a G mm grid together with
its net id; when a net is routed, a Euclidean distance transform of all
*foreign* copper gives, per grid point, the distance to the nearest foreign
copper.  A track centre line may only visit points whose distance is at least
width/2 + clearance + G/2 (the G/2 term absorbs rasterisation error).
The result is always re-checked with KiCad's DRC afterwards.
"""

import heapq
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), "build")

G = 0.2            # grid pitch, mm
CLR = 0.2          # copper clearance, mm
EDGE = 0.4         # copper to board edge, mm (OSH Park min 15 mil = 0.381)
VIA_COST = 2.0     # mm-equivalent cost of a via
TURN_COST = 0.2    # per 45 degree direction change
DIAG = 0.05        # extra track margin: a 45-degree segment between grid points can pass
                   # a pad corner closer than its grid vertices (DRC hit 0.179 mm, v1.7)
WIDTH = {"signal": 0.25, "power": 0.5, "GND": 0.4}
VIA = {"signal": (0.6, 0.3), "power": (0.8, 0.4), "GND": (0.6, 0.3)}
LAYERS = ("F", "B")
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def point_in_poly(X, Y, poly):
    inside = np.zeros(X.shape, bool)
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]
        x2, y2 = poly[(k + 1) % n]
        cond = ((y1 > Y) != (y2 > Y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (x2 - x1) * (Y - y1) / (y2 - y1) + x1
        inside ^= cond & (X < xint)
    return inside


class Board:
    def __init__(self, geom):
        self.geom = geom
        xs = [p[0] for p in geom["outline"]]
        ys = [p[1] for p in geom["outline"]]
        # 1 mm margin so the distance transform "sees" the board edge
        self.x0, self.y0 = min(xs) - 1.0, min(ys) - 1.0
        self.nx = int(round((max(xs) + 1.0 - self.x0) / G)) + 1
        self.ny = int(round((max(ys) + 1.0 - self.y0) / G)) + 1
        self.X, self.Y = np.meshgrid(self.x0 + np.arange(self.nx) * G,
                                     self.y0 + np.arange(self.ny) * G)
        self.inside = point_in_poly(self.X, self.Y, geom["outline"])
        self.dist_edge = ndimage.distance_transform_edt(self.inside) * G
        self.net_names = sorted(geom["nets"])
        self.nid = {n: i + 1 for i, n in enumerate(self.net_names)}
        self.reset()

    def rect_mask(self, bbox, e=0.0):
        x0, y0, x1, y1 = bbox
        return ((self.X >= x0 - e) & (self.X <= x1 + e) &
                (self.Y >= y0 - e) & (self.Y <= y1 + e))

    def reset(self):
        self.own = {l: np.zeros((self.ny, self.nx), np.int32) for l in LAYERS}
        self.failed_pins = []
        self.groups = {}
        self.padmask_all = np.zeros((self.ny, self.nx), bool)
        self.pad_cells = {}
        for l in LAYERS:
            self.own[l][~self.inside] = -1
        for k in self.geom["keepouts"]:
            m = point_in_poly(self.X, self.Y, k["pts"])
            for l in k["layers"]:
                self.own[l][m] = -1
        gid = -2
        for s in self.geom["shapes"]:           # net-tie bridges of solder jumpers
            self.groups[gid] = {self.nid[n] for n in s["nets"]}
            self.own[s["layer"]][self.rect_mask(s["bbox"], G / 2)] = gid
            gid -= 1
        for p in self.geom["pads"]:
            m = self.rect_mask(p["bbox"], G / 2)
            v = self.nid.get(p["net"], -1)
            for l in p["layers"]:
                self.own[l][m] = v
                if p["net"]:
                    self.pad_cells[(p["ref"], p["pin"])] = (l, self.rect_mask(p["bbox"]))
            self.padmask_all |= m
        self.dist_pad = ndimage.distance_transform_edt(~self.padmask_all) * G
        self.tracks, self.vias = [], []

    # -- per-net clearance maps --------------------------------------------
    def free_maps(self, net, kind):
        n = self.nid[net]
        w = WIDTH[kind]
        d, _ = VIA[kind]
        dist = {}
        for l in LAYERS:
            o = self.own[l]
            foreign = (o != 0) & (o != n)
            for g, s in self.groups.items():
                if n in s:
                    foreign &= (o != g)
            dist[l] = ndimage.distance_transform_edt(~foreign) * G
        free = {l: (dist[l] >= w / 2 + CLR + G / 2 + DIAG) & (self.dist_edge >= w / 2 + EDGE + G)
                for l in LAYERS}
        via_ok = ((dist["F"] >= d / 2 + CLR + G / 2) & (dist["B"] >= d / 2 + CLR + G / 2) &
                  (self.dist_edge >= d / 2 + EDGE + G) &
                  (self.dist_pad >= d / 2 + 0.15))
        return free, via_ok

    # -- A* -------------------------------------------------------------------
    def astar(self, free, via_ok, starts, target):
        ny, nx = self.ny, self.nx
        li = {"F": 0, "B": 1}
        tmask = np.zeros((2, ny, nx), bool)
        for l, m in target.items():
            tmask[li[l]] |= m & free[l]
        if not tmask.any():
            return None
        tj, ti = np.nonzero(tmask.any(axis=0))
        ti0, ti1, tj0, tj1 = ti.min(), ti.max(), tj.min(), tj.max()
        fr = np.stack([free["F"], free["B"]])
        vo = via_ok

        def h(i, j):
            dx = max(ti0 - i, 0, i - ti1)
            dy = max(tj0 - j, 0, j - tj1)
            return (max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)) * G

        INF = float("inf")
        gs = {}
        prev = {}
        heap = []
        for l, m in starts.items():
            jj, ii = np.nonzero(m & free[l])
            for j, i in zip(jj.tolist(), ii.tolist()):
                s = (li[l], j, i, 8)
                gs[s] = 0.0
                heapq.heappush(heap, (h(i, j), 0.0, s))
        while heap:
            f, g, s = heapq.heappop(heap)
            if g > gs.get(s, INF):
                continue
            L, j, i, d = s
            if tmask[L, j, i]:
                path = [s]
                while s in prev:
                    s = prev[s]
                    path.append(s)
                return path[::-1]
            for nd, (di, dj) in enumerate(DIRS):
                if d != 8:
                    turn = min((nd - d) % 8, (d - nd) % 8)
                    if turn > 2:
                        continue
                else:
                    turn = 0
                i2, j2 = i + di, j + dj
                if not (0 <= i2 < nx and 0 <= j2 < ny) or not fr[L, j2, i2]:
                    continue
                if di and dj and not (fr[L, j, i2] or fr[L, j2, i]):
                    continue
                ng = g + (math.sqrt(2) if di and dj else 1.0) * G + turn * TURN_COST
                s2 = (L, j2, i2, nd)
                if ng < gs.get(s2, INF):
                    gs[s2] = ng
                    prev[s2] = s
                    heapq.heappush(heap, (ng + h(i2, j2), ng, s2))
            if vo[j, i] and fr[1 - L, j, i]:
                s2 = (1 - L, j, i, 8)
                ng = g + VIA_COST
                if ng < gs.get(s2, INF):
                    gs[s2] = ng
                    prev[s2] = s
                    heapq.heappush(heap, (ng + h(i, j), ng, s2))
        return None

    # -- commit a path ----------------------------------------------------------
    def seg_mask(self, x1, y1, x2, y2, r):
        X, Y = self.X, self.Y
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return (X - x1) ** 2 + (Y - y1) ** 2 <= r * r
        t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
        return (X - (x1 + t * dx)) ** 2 + (Y - (y1 + t * dy)) ** 2 <= r * r

    def commit(self, net, kind, path, tree):
        n = self.nid[net]
        w = WIDTH[kind]
        d, drill = VIA[kind]
        names = ("F", "B")
        xy = lambda s: (round(self.x0 + s[2] * G, 4), round(self.y0 + s[1] * G, 4))
        # split by layer, keep only corner points
        runs, cur = [], [path[0]]
        for s in path[1:]:
            if s[0] != cur[-1][0]:
                runs.append(cur)
                self.vias.append({"net": net, "x": xy(s)[0], "y": xy(s)[1], "d": d, "drill": drill})
                m = self.seg_mask(*xy(s), *xy(s), d / 2 + G / 2)
                for l in LAYERS:
                    self.own[l][m & (self.own[l] == 0)] = n
                    tree[l] |= m
                cur = [s]
            else:
                cur.append(s)
        runs.append(cur)
        for run in runs:
            l = names[run[0][0]]
            pts = [xy(run[0])]
            for a, b, c in zip(run, run[1:], run[2:]):
                if (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]):
                    pts.append(xy(b))
            if len(run) > 1:
                pts.append(xy(run[-1]))
            for p, q in zip(pts, pts[1:]):
                self.tracks.append({"net": net, "layer": l, "x1": p[0], "y1": p[1],
                                    "x2": q[0], "y2": q[1], "w": w})
                m = self.seg_mask(p[0], p[1], q[0], q[1], w / 2 + G / 2)
                self.own[l][m & (self.own[l] == 0)] = n
                tree[l] |= m

    def route_net(self, net):
        info = self.geom["nets"][net]
        kind = "GND" if net == "GND" else ("power" if info["power"] else "signal")
        pins = [tuple(p) for p in info["pins"] if tuple(p) in self.pad_cells]
        if len(pins) < 2:
            return True
        empty = lambda: {l: np.zeros((self.ny, self.nx), bool) for l in LAYERS}
        tree = empty()
        l0, m0 = self.pad_cells[pins[0]]
        tree[l0] |= m0
        todo = pins[1:]
        ok = True
        while todo:
            # nearest remaining pin to the current tree
            cy = {l: np.nonzero(tree[l]) for l in LAYERS}
            pts = np.concatenate([np.stack(cy[l], 1) for l in LAYERS if len(cy[l][0])])

            def dist(pin):
                _, m = self.pad_cells[pin]
                jj, ii = np.nonzero(m)
                c = np.array([jj.mean(), ii.mean()])
                return np.min(np.hypot(*(pts - c).T))
            todo.sort(key=dist)
            pin = todo.pop(0)
            free, via_ok = self.free_maps(net, kind)
            l, m = self.pad_cells[pin]
            tgt = empty()
            tgt[l] |= m
            path = self.astar(free, via_ok, tree, tgt)
            if path is None:
                print(f"   FAILED {net} -> {pin}")
                self.failed_pins.append((net, pin))
                ok = False
                continue
            self.commit(net, kind, path, tree)
            tree[l] |= m
        return ok


from design import SIGNALS                  # noqa: E402
REQUIRED = {s[0] for s in SIGNALS[:8]} | {"VSYS", "VBUS", "+3V3", "VIN", "3V3_NANO"}


def net_order(geom, board):
    def length(net):
        cells = [board.pad_cells[tuple(p)] for p in geom["nets"][net]["pins"]
                 if tuple(p) in board.pad_cells]
        cs = []
        for _, m in cells:
            jj, ii = np.nonzero(m)
            cs.append((ii.mean() * G, jj.mean() * G))
        return sum(math.dist(a, b) for a, b in zip(cs, cs[1:]))
    required = REQUIRED
    nets = [n for n in geom["nets"] if n != "GND"]
    power = sorted([n for n in nets if geom["nets"][n]["power"]], key=length, reverse=True)
    req = sorted([n for n in nets if n in required and not geom["nets"][n]["power"]],
                 key=length, reverse=True)
    opt = sorted([n for n in nets if not geom["nets"][n]["power"] and n not in required],
                 key=length, reverse=True)
    return power + req + opt + ["GND"]


def main():
    geom = json.load(open(os.path.join(BUILD, "geometry.json")))
    board = Board(geom)
    order = net_order(geom, board)
    best = None
    gnd_try = 0
    for it in range(12):
        board.reset()
        failed = []
        print(f"pass {it + 1}: order {order[:6]}...")
        for net in order:
            if not board.route_net(net):
                failed.append(net)
        print(f"pass {it + 1}: {len(failed)} failed {failed}")
        real = [n for n in failed if n != "GND"]   # GND is completed by the pours
        gnd_fail = sorted(p for n, p in board.failed_pins if n == "GND")
        score = (len(real), len(gnd_fail))
        if best is None or score < best[0]:
            best = (score, list(board.tracks), list(board.vias), failed)
        if not real and not gnd_fail:
            break
        if not real and gnd_try < 2:
            # Unrouted GND pins are left to the pours, but a pin boxed in by
            # other nets' vias becomes an isolated island (seen on U1-33 AGND).
            # Retry with GND routed before the optional (spare) nets.
            gnd_try += 1
            req_end = max(order.index(n) for n in order if n in REQUIRED) + 1
            order = [n for n in order[:req_end] if n != "GND"] + ["GND"] +                     [n for n in order[req_end:] if n != "GND"]
            continue
        if not real:
            break
        order = failed + [n for n in order if n not in failed]
        if "GND" in order and gnd_try == 0:
            order.remove("GND")
            order.append("GND")
    _score, tracks, vias, failed = best
    with open(os.path.join(BUILD, "routes.json"), "w") as f:
        json.dump({"tracks": tracks, "vias": vias, "failed": failed}, f, indent=1)
    print(f"routes written: {len(tracks)} segments, {len(vias)} vias, failed nets: {failed}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
