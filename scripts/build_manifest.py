"""Build the public catalog without importing submitted plugin code."""

import argparse
import ast
import json
import re
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = {
    "trigger",
    "data_in",
    "metadata_in",
    "checks",
    "sequence",
    "data_transfer",
    "checkpoint",
    "encode",
    "process",
    "data_out",
    "metadata_out",
    "goal",
    "solver",
    "services",
    "extensions",
}


def build(ref):
    rows = []
    for path in sorted((ROOT / "plugins/autostacgis_plugins").glob("*.py")):
        if path.name.startswith("_"):
            continue
        declarations = {}
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "IMPLEMENTATIONS":
                        raise ValueError(
                            f"{path}: plural IMPLEMENTATIONS is forbidden; declare one CAPABILITY"
                        )
                    if isinstance(target, ast.Name) and target.id in (
                        "ID",
                        "VERSION",
                        "CAPABILITY",
                        "REQUIRES",
                        "DEPENDENCIES",
                        "DESCRIPTION",
                    ):
                        declarations[target.id] = ast.literal_eval(node.value)
        assert declarations["CAPABILITY"] in CAPABILITIES, f"{path}: one CAPABILITY required"
        assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", declarations["VERSION"]), (
            f"{path}: semantic VERSION required"
        )
        assert isinstance(declarations["REQUIRES"], (list, tuple)), f"{path}: literal REQUIRES required"
        rows.append(
            {
                "id": declarations["ID"],
                "version": declarations["VERSION"],
                "capability": declarations["CAPABILITY"],
                "requires": list(declarations["REQUIRES"]),
                "dependencies": list(declarations.get("DEPENDENCIES", [])),
                "description": declarations.get(
                    "DESCRIPTION", ast.get_docstring(ast.parse(path.read_text())) or ""
                ),
                "module": f"autostacgis_plugins.{path.stem}",
                "source": {
                    "repository": "https://github.com/autostacgis/autostacgis-plugins",
                    "ref": ref,
                    "path": str(path.relative_to(ROOT)),
                    "url": f"https://raw.githubusercontent.com/autostacgis/autostacgis-plugins/{ref}/{path.relative_to(ROOT)}",
                    "sha256": sha256(path.read_bytes()).hexdigest(),
                },
            }
        )
    names = [row["id"] for row in rows]
    assert len(names) == len(set(names)), "Plugin IDs must be globally unique"
    by_name = {row["id"]: row for row in rows}

    def visit(name, active=()):
        assert name not in active, f"Recursive plugin requirements: {active} -> {name}"
        for dependency in by_name[name]["requires"]:
            assert dependency in by_name, f"{name}: unknown requirement {dependency}"
            visit(dependency, (*active, name))

    for name in names:
        visit(name)
    return {
        "format_version": 1,
        "namespace": "autostacgis_plugins",
        "plugins": sorted(rows, key=lambda row: row["id"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="main")
    parser.add_argument("--output", default="plugins.json")
    parser.add_argument("--check-base")
    args = parser.parse_args()
    result = build(args.ref)
    if args.check_base:
        import subprocess

        for row in result["plugins"]:
            path = row["source"]["path"]
            previous = subprocess.run(
                ["git", "show", f"{args.check_base}:{path}"], cwd=ROOT, capture_output=True, text=True
            )
            if previous.returncode or previous.stdout == (ROOT / path).read_text():
                continue
            for node in ast.parse(previous.stdout).body:
                if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets
                ):
                    assert ast.literal_eval(node.value) != row["version"], (
                        f"{path}: bump VERSION when changing a plugin"
                    )
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
