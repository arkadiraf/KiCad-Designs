#!/usr/bin/env python3
"""Verify the schematic connectivity exported by KiCad against design.py.

usage: check_netlist.py <kicad .net file>
"""
import re
import sys
from design import build_nets


def parse(path):
    txt = open(path).read()
    nets = {}
    # whitespace-tolerant: KiCad 7 writes one net per line, KiCad 8+ one token per line
    for m in re.finditer(r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)', txt, re.S):
        name = m.group(1).lstrip("/")
        nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', m.group(2))
        nets[name] = sorted(n for n in nodes if not n[0].startswith("#"))
    return nets


def main():
    got = parse(sys.argv[1])
    want = {k: sorted(v) for k, v in build_nets().items()}
    ok = True
    # compare as sets of connections (net names may be prefixed differently)
    got_sets = {frozenset(v) for v in got.values() if len(v) > 0}
    for net, conns in want.items():
        if frozenset(conns) not in got_sets:
            ok = False
            match = [g for g, v in got.items() if set(v) & set(conns)]
            print(f"MISMATCH {net}: want {conns}; found in {[(g, got[g]) for g in match]}")
    for g, v in got.items():
        if len(v) > 1 and frozenset(v) not in {frozenset(c) for c in want.values()}:
            ok = False
            print(f"EXTRA net {g}: {v}")
    names_ok = all(n in got for n in want)
    print("net names match" if names_ok else
          f"net names missing: {[n for n in want if n not in got]}")
    print("NETLIST OK" if ok else "NETLIST ERRORS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
