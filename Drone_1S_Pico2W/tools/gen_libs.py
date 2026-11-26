#!/usr/bin/env python3
"""Write the sym-lib-table and fp-lib-table of both boards (Frame/, FC/).

All custom symbols and footprints live in the repository's shared libraries,
KiCad-Designs/Libraries (KD_Power, KD_Sensors, KD_Modules, KD_Connectors), so other
designs can reuse them. They are generated there by Libraries/tools/gen_lib.py; this
script regenerates them first, then points both boards at them through ${KIPRJMOD}.
Sources and verification status of each part: Libraries/README.md.
"""

import os
import subprocess
import sys

from design import SHARED_LIBS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIBDIR = os.path.normpath(os.path.join(ROOT, SHARED_LIBS))

sys.path.insert(0, os.path.join(LIBDIR, "tools"))
import gen_lib  # noqa: E402  (shared library generator)


def write_tables():
    rel = "../" + SHARED_LIBS        # ${KIPRJMOD} is Frame/ or FC/, one below ROOT
    sym, fp = gen_lib.lib_table_entries(rel)
    for board in ("Frame", "FC"):
        with open(os.path.join(ROOT, board, "fp-lib-table"), "w") as f:
            f.write("(fp_lib_table\n" + "\n".join(fp) + "\n)\n")
        with open(os.path.join(ROOT, board, "sym-lib-table"), "w") as f:
            f.write("(sym_lib_table\n" + "\n".join(sym) + "\n)\n")
        print(f"wrote {board}/fp-lib-table, {board}/sym-lib-table -> {rel}")


if __name__ == "__main__":
    subprocess.run([sys.executable, os.path.join(LIBDIR, "tools", "gen_lib.py")], check=True)
    write_tables()
