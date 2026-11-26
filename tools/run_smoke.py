"""Execute all main-directory notebooks in isolated IPython processes.

No notebook outputs are overwritten. This runner also works in environments
where Jupyter cannot open the sockets needed for a separate kernel.
"""

import argparse
from contextlib import ExitStack, chdir
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# The text immediately before this example explains why it must raise.
EXPECTED_ERRORS = {("14-Adaptive-Filtering.ipynb", 92): ("ValueError", "All filters must have the same state dimension")}


def execute(name):
    from IPython.terminal.interactiveshell import TerminalInteractiveShell
    from IPython.utils.capture import capture_output

    with ExitStack() as stack:
        directory = stack.enter_context(tempfile.TemporaryDirectory(prefix="kalman-smoke-"))
        work = Path(directory) / "book"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", ".venv", "build", "__pycache__"))
        stack.enter_context(chdir(work))
        sys.path.insert(0, str(work))
        notebook = json.loads((work / name).read_text(encoding="utf-8"))
        shell = TerminalInteractiveShell.instance()
        count = expected_count = 0
        for i, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            with capture_output() as captured:
                result = shell.run_cell("".join(cell["source"]), store_history=False)
            count += 1
            expected = EXPECTED_ERRORS.get((name, i))
            error = result.error_before_exec or result.error_in_exec
            if expected:
                if error is None or type(error).__name__ != expected[0] or str(error) != expected[1]:
                    raise AssertionError(f"{name} cell {i}: expected {expected}, got {error!r}")
                expected_count += 1
            elif error is not None:
                print(captured.stdout, file=sys.stderr)
                raise RuntimeError(f"{name} cell {i}: {type(error).__name__}: {error}") from error
        print(f"PASS: {name}: {count} code cells, {expected_count} expected exceptions")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebooks", nargs="*", help="main-directory filenames; defaults to all")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        execute(args.worker)
        return
    available = {path.name for path in ROOT.glob("*.ipynb")}
    names = args.notebooks or sorted(available)
    for name in names:
        if name not in available:
            parser.error(f"not a main-directory notebook: {name}")
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", name],
            env={**os.environ, "MPLBACKEND": "Agg", "OPENBLAS_NUM_THREADS": "1"},
            timeout=300,
        )
        if completed.returncode:
            raise SystemExit(completed.returncode)
    print(f"PASS: {len(names)} notebooks executed; source files and cached outputs unchanged.")


if __name__ == "__main__":
    main()
