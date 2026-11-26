#!/usr/bin/env python3
"""Check firmware/overlay/pinout_definitions.py against the board (design.py)."""
import os
import re
import sys
from design import SIGNALS, NANO_PINS

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "firmware", "overlay", "pinout_definitions.py")).read()
fw = {m.group(1): int(m.group(2)) for m in re.finditer(r"(?m)^([AD]\d+) = (\d+)\b", src)}
nc = set(re.findall(r"(?m)^(D\d+(?: = D\d+)*) = None", src)[0].split(" = ")) if "None" in src else set()

ok = True
board = {}
for net, npin, _ppin, gpio, _c in SIGNALS:
    name = NANO_PINS[npin].split("/")[0]
    board[name] = int(gpio[2:])
for name, gp in board.items():
    if fw.get(name) != gp:
        ok = False
        print(f"MISMATCH {name}: board GP{gp}, firmware {fw.get(name)}")
for name in fw:
    if name not in board:
        ok = False
        print(f"firmware defines {name}={fw[name]} but the board does not wire it")
for name in nc:
    if name in board:
        ok = False
        print(f"firmware says {name} not wired, board wires it to GP{board[name]}")
print(f"{len(board)} wired Nano pins checked;", "FIRMWARE OK" if ok else "FIRMWARE MISMATCH")
sys.exit(0 if ok else 1)
