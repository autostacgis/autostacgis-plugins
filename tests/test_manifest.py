"""The published catalog must describe the exact reviewed source bytes."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_committed_manifest_matches_all_versioned_plugin_sources():
    build = runpy.run_path(str(ROOT / "scripts/build_manifest.py"))["build"]
    expected = build("main")
    assert len(expected["plugins"]) == 82
    assert json.loads((ROOT / "plugins.json").read_text()) == expected
