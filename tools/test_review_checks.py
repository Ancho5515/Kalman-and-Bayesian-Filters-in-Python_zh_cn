"""Regression coverage for rendered links and narrowly reviewed code changes."""

import json
from pathlib import Path
import tempfile
import unittest

from check_translation import (
    ROOT, RenderedAnchors, check_cross_notebook_links, check_file,
    check_local_links, check_rendered_anchors,
)


def parse(body):
    result = RenderedAnchors()
    result.feed(body)
    result.close()
    return result


class ReviewChecks(unittest.TestCase):
    def test_markdown_local_links_ignore_code_and_allow_encoded_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "README.md"
            (path.parent / "中文.md").write_text("target")
            text = "[ok](%E4%B8%AD%E6%96%87.md)\n```python\n# [example](missing.py)\n```"
            self.assertEqual(check_local_links(path, text), [])
            self.assertEqual(len(check_local_links(path, text + "\n[bad](absent.md)")), 1)

    def test_unicode_and_legacy_same_notebook_anchors(self):
        body = '<h2 id="均值">均值</h2><a href="#%E5%9D%87%E5%80%BC">go</a><a name="[1]"></a><a href="#[1]">ref</a>'
        self.assertEqual(check_rendered_anchors(body), [])
        self.assertEqual(len(check_rendered_anchors(body + '<a href="#absent">bad</a>')), 1)

    def test_cross_notebook_fragment_is_checked_on_destination(self):
        origin = (ROOT / "Supporting_Notebooks/origin.ipynb").resolve()
        target = (ROOT / "03-Gaussians.ipynb").resolve()
        links = {origin: parse('<a href="../03-Gaussians.ipynb#%E5%9D%87%E5%80%BC">go</a>'),
                 target: parse('<h2 id="均值">target</h2>')}
        self.assertEqual(check_cross_notebook_links(links), [])
        links[target] = parse('<h2 id="other">target</h2>')
        self.assertIn("missing cross-notebook anchor", check_cross_notebook_links(links)[0])
        del links[target]
        self.assertIn("unrendered notebook link", check_cross_notebook_links(links)[0])

    def test_reviewed_correction_does_not_allow_other_code_changes(self):
        manifest = json.loads((ROOT / "translation/source_manifest.json").read_text())
        name = "12-Particle-Filters.ipynb"
        spec = manifest["notebooks"][name]
        approved = [item for item in manifest["reviewed_algorithm_changes"] if item["file"] == name]
        markdown = [item for item in manifest["reviewed_markdown_changes"] if item["file"] == name]
        self.assertEqual(check_file(ROOT / name, spec, approved, markdown), [])
        nb = json.loads((ROOT / name).read_text())
        cell = next(cell for i, cell in enumerate(nb["cells"]) if cell["cell_type"] == "code" and i != 65)
        cell["source"].append("\nraise RuntimeError('unexpected change')\n")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text(json.dumps(nb))
            failures = check_file(path, spec, approved, markdown)
        self.assertTrue(any("code/raw cells" in error for error in failures))

    def test_reviewed_algorithm_is_checked_exactly(self):
        manifest = json.loads((ROOT / "translation/source_manifest.json").read_text())
        name = "12-Particle-Filters.ipynb"
        approved = [item for item in manifest["reviewed_algorithm_changes"] if item["file"] == name]
        markdown = [item for item in manifest["reviewed_markdown_changes"] if item["file"] == name]
        nb = json.loads((ROOT / name).read_text())
        nb["cells"][65]["source"].append("\n# unexpected edit\n")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text(json.dumps(nb))
            failures = check_file(path, manifest["notebooks"][name], approved, markdown)
        self.assertTrue(any("reviewed algorithm correction changed" in error for error in failures))

    def test_reviewed_formula_does_not_allow_other_formula_changes(self):
        manifest = json.loads((ROOT / "translation/source_manifest.json").read_text())
        name = "03-Gaussians.ipynb"
        markdown = [item for item in manifest["reviewed_markdown_changes"] if item["file"] == name]
        spec = manifest["notebooks"][name]
        self.assertEqual(check_file(ROOT / name, spec, reviewed_markdown=markdown), [])
        self.assertTrue(check_file(ROOT / name, spec))  # correction must be declared
        nb = json.loads((ROOT / name).read_text())
        cell = nb["cells"][111]
        cell["source"] = [line.replace(r"\mu_x = \mu_p + \mu_z", r"\mu_x = \mu_p - \mu_z") for line in cell["source"]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text(json.dumps(nb))
            failures = check_file(path, spec, reviewed_markdown=markdown)
        self.assertTrue(any("source display equation" in error for error in failures))


if __name__ == "__main__":
    unittest.main(verbosity=2)
