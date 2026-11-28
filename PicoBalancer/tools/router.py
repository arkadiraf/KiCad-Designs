#!/usr/bin/env python3
"""2-layer grid router (A*, 45-degree moves, vias) - adapted from Pico_Alvik_Adapter/tools/router.py.

Reads  build/geometry.json  (tools/gen_pcb.py geom: pads, keep-outs AND the hand-routed tracks / vias of routes.py)
Writes build/routes.json    (consumed by tools/gen_pcb.py finish)

PicoBalancer changes: existing copper (hand routing) is an obstacle for foreign nets and part of its own net; each net
is split into connected groups (pads + existing copper, joined across layers only at vias and through-hole pads) and
the router joins the groups, so an escape stub at each end of a net is not mistaken for a finished connection.
Clearance model as before: distance transform of foreign copper on a G grid; re-checked with KiCad DRC afterwards.
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

G = 0.2            # grid pitch, mm (fine-pitch pins are escaped by hand in routes.py)
CLR = 0.2          # copper clearance, mm
EDGE = 0.4         # copper to board edge, mm
VIA_COST = 2.0
TURN_COST = 0.2
DIAG = 0.05
WIDTH = {"signal": 0.25, "power": 0.4, "GND": 0.4}
VIA = {"signal": (0.6, 0.3), "power": (0.6, 0.3), "GND": (0.6, 0.3)}
LAYERS = ("F", "B")
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
POWER_KIND = {"3V3"}       # remaining power-like nets routed at 0.4 mm


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
                self.pad_cells.setdefault((p["ref"], p["pin"]), []).append((tuple(p["layers"]), self.rect_mask(p["bbox"])))
            self.padmask_all |= m
        self.dist_pad = ndimage.distance_transform_edt(~self.padmask_all) * G
        self.tracks, self.vias = [], []
        # existing copper (hand routing): obstacle for foreign nets, part of its own net
        self.exist = {}                      # net -> {layer: mask}
        self.exist_via = {}                  # net -> mask of via / through-hole cells (layer joints)
        for t in self.geom.get("tracks", []):
            m = self.seg_mask(t["x1"], t["y1"], t["x2"], t["y2"], t["w"] / 2 + G / 2)
            v = self.nid.get(t["net"], -1)
            self.own[t["layer"]][m] = v
            e = self.exist.setdefault(t["net"], {l: np.zeros((self.ny, self.nx), bool) for l in LAYERS})
            e[t["layer"]] |= self.seg_mask(t["x1"], t["y1"], t["x2"], t["y2"], t["w"] / 2)
        for vv in self.geom.get("vias", []):
            m = self.seg_mask(vv["x"], vv["y"], vv["x"], vv["y"], vv["d"] / 2 + G / 2)
            v = self.nid.get(vv["net"], -1)
            core = self.seg_mask(vv["x"], vv["y"], vv["x"], vv["y"], vv["d"] / 2)
            for l in LAYERS:
                self.own[l][m] = v
                e = self.exist.setdefault(vv["net"], {ll: np.zeros((self.ny, self.nx), bool) for ll in LAYERS})
                e[l] |= core
            self.exist_via[vv["net"]] = self.exist_via.get(vv["net"], np.zeros((self.ny, self.nx), bool)) | core
            self.padmask_all |= m
        self.dist_pad = ndimage.distance_transform_edt(~self.padmask_all) * G

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
    def astar(self, free, via_ok, starts, target, margin=None):
        ny, nx = self.ny, self.nx
        if margin is not None:              # search window: target box + margin, seeds inside it only
            tj_, ti_ = np.nonzero(np.logical_or.reduce([m for m in target.values()]))
            if len(tj_) == 0:
                return None
            k = int(margin / G)
            wj0, wj1 = max(tj_.min() - k, 0), min(tj_.max() + k, ny - 1)
            wi0, wi1 = max(ti_.min() - k, 0), min(ti_.max() + k, nx - 1)
            win = np.zeros((ny, nx), bool)
            win[wj0:wj1 + 1, wi0:wi1 + 1] = True
            starts = {l: m & win for l, m in starts.items()}
            if not any(m.any() for m in starts.values()):
                return None
            free = {l: m & win for l, m in free.items()}
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

    def groups_of(self, net):
        """Connected groups of the net: pads + existing copper, joined across layers at vias / through-hole pads."""
        info = self.geom["nets"][net]
        lay = {l: np.zeros((self.ny, self.nx), bool) for l in LAYERS}
        joint = self.exist_via.get(net, np.zeros((self.ny, self.nx), bool)).copy()
        for pin in info["pins"]:
            for layers, m in self.pad_cells.get(tuple(pin), []):
                for l in layers:
                    lay[l] |= m
                if len(layers) == 2:
                    joint |= m
        for l, m in self.exist.get(net, {}).items():
            lay[l] |= m
        st = np.ones((3, 3), bool)
        lab = {}
        off = 0
        for l in LAYERS:
            a, n = ndimage.label(lay[l], structure=st)
            a[a > 0] += off
            lab[l] = a
            off += n
        parent = list(range(off + 1))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        jj, ii = np.nonzero(joint & (lab["F"] > 0) & (lab["B"] > 0))
        for j, i in zip(jj, ii):
            a, b = find(lab["F"][j, i]), find(lab["B"][j, i])
            if a != b:
                parent[a] = b
        comps = {}
        for l in LAYERS:
            for k in np.unique(lab[l]):
                if k == 0:
                    continue
                r = find(k)
                c = comps.setdefault(r, {ll: np.zeros((self.ny, self.nx), bool) for ll in LAYERS})
                c[l] |= lab[l] == k
        # keep only groups that contain a pad of the net (stray copper is ignored)
        out = []
        for c in comps.values():
            has_pad = False
            for pin in info["pins"]:
                for layers, m in self.pad_cells.get(tuple(pin), []):
                    if any((c[l] & m).any() for l in layers):
                        has_pad = True
            out.append(c if has_pad else c)
        return out

    def route_net(self, net):
        kind = "GND" if net == "GND" else ("power" if (net in POWER_KIND or self.geom["nets"][net]["power"]) else "signal")
        comps = self.groups_of(net)
        if len(comps) < 2:
            return True
        tree = comps[0]
        todo = comps[1:]
        ok = True
        fm = None
        while todo:
            cy = [np.stack(np.nonzero(tree[l]), 1) for l in LAYERS if tree[l].any()]
            pts = np.concatenate(cy)

            def dist(c):
                best = 1e9
                for l in LAYERS:
                    if c[l].any():
                        jj, ii = np.nonzero(c[l])
                        k = len(jj) // 2
                        best = min(best, np.min(np.hypot(pts[:, 0] - jj[k], pts[:, 1] - ii[k])))
                return best
            todo.sort(key=dist)
            c = todo.pop(0)
            if fm is None:
                fm = self.free_maps(net, kind)
            free, via_ok = fm
            path = None
            for margin in (6.0, 15.0, 40.0, None):
                path = self.astar(free, via_ok, tree, c, margin)
                if path is not None:
                    break
            if path is None:
                jj, ii = np.nonzero(c["F"] | c["B"])
                print(f"   FAILED {net} near ({self.x0 + ii.mean() * G:.1f}, {self.y0 + jj.mean() * G:.1f})")
                self.failed_pins.append((net, (round(self.x0 + ii.mean() * G, 1), round(self.y0 + jj.mean() * G, 1))))
                ok = False
                continue
            self.commit(net, kind, path, tree)
            for l in LAYERS:
                tree[l] |= c[l]
        return ok


def net_order(geom, board):
    def length(net):
        xs = [(np.nonzero(m)[1].mean(), np.nonzero(m)[0].mean()) for p in geom["nets"][net]["pins"]
              for _, m in board.pad_cells.get(tuple(p), [])[:1]]
        return sum(math.dist(a, b) for a, b in zip(xs, xs[1:])) * G
    nets = [n for n in geom["nets"] if n != "GND"]
    power = sorted([n for n in nets if geom["nets"][n]["power"] or n in POWER_KIND], key=length, reverse=True)
    sig = sorted([n for n in nets if n not in power], key=length, reverse=True)
    return power + sig + ["GND"]


def main():
    geom = json.load(open(os.path.join(BUILD, "geometry.json")))
    board = Board(geom)
    order = net_order(geom, board)
    best = None
    for it in range(int(os.environ.get("ROUTER_PASSES", "4"))):
        board.reset()
        failed = []
        print(f"pass {it + 1}: {len(order)} nets")
        for k, net in enumerate(order):
            print(f"  [{k + 1}/{len(order)}] {net}", flush=True)
            if not board.route_net(net):
                failed.append(net)
        real = [n for n in failed if n != "GND"]
        gnd_fail = [p for n, p in board.failed_pins if n == "GND"]
        print(f"pass {it + 1}: failed {failed}, GND groups left to the pours: {len(gnd_fail)}")
        score = (len(real), len(gnd_fail))
        if best is None or score < best[0]:
            best = (score, list(board.tracks), list(board.vias), failed, list(board.failed_pins))
        if not real:
            break
        order = real + [n for n in order if n not in real]
    _s, tracks, vias, failed, fp = best
    with open(os.path.join(BUILD, "routes.json"), "w") as f:
        json.dump({"tracks": tracks, "vias": vias, "failed": failed, "failed_pins": fp}, f, indent=1)
    print(f"routes written: {len(tracks)} segments, {len(vias)} vias, failed nets: {failed}")
    return 0 if not [n for n in failed if n != "GND"] else 1


if __name__ == "__main__":
    sys.exit(main())
