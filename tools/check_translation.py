"""Check translation invariants without fetching Git history or starting a kernel."""

import argparse
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DISPLAY_MATH = re.compile(r"(?<!\\)\$\$.*?(?<!\\)\$\$", re.S)
FENCES = re.compile(r"```.*?```", re.S)
LINKS = re.compile(r"\]\(([^)]+)\)|(?:src|href)=[\"']([^\"']+)")


class RenderedAnchors(HTMLParser):
    """Read actual rendered targets, including legacy <a name=...> anchors."""

    def __init__(self):
        super().__init__()
        self.targets = set()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for target in (attrs.get("id"), attrs.get("name") if tag == "a" else None):
            if target:
                self.targets.add(unquote(target))
        if tag == "a" and attrs.get("href"):
            parts = urlsplit(attrs["href"])
            if not (parts.scheme or parts.netloc or parts.path) and parts.fragment:
                self.links.add(parts.fragment)


def check_rendered_anchors(body):
    parsed = RenderedAnchors()
    parsed.feed(body)
    parsed.close()
    return [
        f"missing same-notebook anchor #{fragment}"
        for fragment in sorted(parsed.links)
        if unquote(fragment) not in parsed.targets
    ]


def cells(notebook):
    if "cells" in notebook:
        return notebook["cells"]
    return [cell for sheet in notebook.get("worksheets", []) for cell in sheet["cells"]]


def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def protected_content(notebook):
    result = deepcopy(notebook)
    for cell in cells(result):
        if cell["cell_type"] == "markdown":
            cell.pop("source", None)
    return result


def check_file(path, expected):
    import nbformat

    notebook = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    # Read the native version: legacy experiment notebooks use nbformat 3.
    nbformat.validate(nbformat.reads(json.dumps(notebook), as_version=nbformat.NO_CONVERT))
    if digest(protected_content(notebook)) != expected["protected_sha256"]:
        errors.append("code/raw cells, outputs, cell ordering, or metadata changed")
    actual_cells = cells(notebook)
    if len(actual_cells) != expected["cell_count"]:
        errors.append("cell count changed")
    for index, spec in expected["markdown"].items():
        i = int(index)
        if i >= len(actual_cells) or actual_cells[i]["cell_type"] != "markdown":
            errors.append(f"cell {i}: expected markdown")
            continue
        source = "".join(actual_cells[i]["source"])
        if any(ord(ch) < 32 and ch not in "\n\r\t" for ch in source):
            errors.append(f"cell {i}: unexpected control character")
        if digest(DISPLAY_MATH.findall(source)) != spec["display_math_sha256"]:
            errors.append(f"cell {i}: a source display equation was changed or lost")
        if digest(FENCES.findall(source)) != spec["fenced_code_sha256"]:
            errors.append(f"cell {i}: fenced example code was changed or lost")
        if spec.get("chinese_required") and not re.search(r"[\u4e00-\u9fff]", source):
            errors.append(f"cell {i}: Chinese prose is missing")
        for match in LINKS.finditer(FENCES.sub("", source)):
            target = match[1] or match[2]
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            linked_path = path.parent / unquote(parts.path)
            if not linked_path.is_file():
                errors.append(f"cell {i}: missing local link {target}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", type=Path, help="also export every notebook to this HTML directory")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "translation/source_manifest.json").read_text(encoding="utf-8"))
    expected = manifest["notebooks"]
    actual = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*.ipynb")
        if not any(part in {".git", ".venv", "build", ".ipynb_checkpoints"} for part in p.relative_to(ROOT).parts)
    }
    failures = []
    if actual != set(expected):
        failures.append(f"Notebook inventory changed: {sorted(actual ^ set(expected))}")
    exporter = None
    if args.render:
        from nbconvert import HTMLExporter
        exporter = HTMLExporter()
        # The original notebooks contain trusted HTML, images, and math.
        exporter.exclude_input_prompt = True
        exporter.exclude_output_prompt = True
    for relative, spec in expected.items():
        path = ROOT / relative
        try:
            for error in check_file(path, spec):
                failures.append(f"{relative}: {error}")
            if exporter is not None:
                import nbformat
                rendered = nbformat.read(path, as_version=4)
                # Older saved notebooks may contain pre-Jupyter widget metadata
                # without a usable widget-state MIME entry. Keep the source
                # intact and omit only that unusable metadata from the export.
                widgets = rendered.metadata.get("widgets")
                if widgets is not None and "application/vnd.jupyter.widget-state+json" not in widgets:
                    rendered.metadata.pop("widgets")
                body, _ = exporter.from_notebook_node(rendered)
                for error in check_rendered_anchors(body):
                    failures.append(f"{relative}: {error}")
                target = args.render / Path(relative).with_suffix(".html")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body, encoding="utf-8")
        except Exception as exc:
            failures.append(f"{relative}: {type(exc).__name__}: {exc}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    count = sum(len(item["markdown"]) for item in expected.values())
    print(f"PASS: {len(expected)} notebooks, {count} markdown cells; protected content, equations, code fences, Chinese prose, and local links checked.")
    if exporter:
        print(f"PASS: {len(expected)} HTML exports in {args.render}; same-notebook anchors checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
