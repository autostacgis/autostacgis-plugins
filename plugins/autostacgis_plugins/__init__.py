"""Discover self-contained plugin modules."""

from copy import deepcopy
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from pkgutil import extend_path, iter_modules

__path__ = extend_path(__path__, __name__)
# Spawned pool workers must be able to import active plugin classes before
# unpickling a task, without relying on their parent's in-memory import state.
import json
import os

_store = Path(os.environ.get("AUTOSTACGIS_PLUGIN_DIR", Path.home() / ".autostacgis/plugins"))
_index = _store / "installed.json"
if _index.exists():
    for _row in json.loads(_index.read_text()).values():
        _folder = (_store / _row["path"]).resolve().parent
        if not _folder.is_relative_to(_store.resolve()):
            raise ValueError("Invalid installed plugin namespace path")
        if sha256((_store / _row["path"]).read_bytes()).hexdigest() != _row["sha256"]:
            raise ValueError("Installed plugin integrity check failed")
        if str(_folder) not in __path__:
            __path__.insert(0, str(_folder))


def modules():
    return sorted(
        (
            import_module(f"{__name__}.{e.name}")
            for e in iter_modules([str(Path(__file__).parent)])
            if not e.name.startswith("_")
        ),
        key=lambda m: m.ID,
    )


def definition(module):
    from autostacgis import Registry

    Registry.validate_module(module)
    implementation = module.IMPLEMENTATION
    return {
        "id": module.ID,
        "requires": list(module.REQUIRES),
        "capabilities": {
            module.CAPABILITY: {
                "implementation": module.ID,
                "settings": getattr(module, "DEFAULTS", {}),
                **(
                    {"contract": deepcopy(implementation.contract)}
                    if module.CAPABILITY in ("goal", "solver")
                    else {}
                ),
                **{
                    field: getattr(implementation, field)
                    for field in ("input_types", "output_types")
                    if hasattr(implementation, field)
                },
            }
        },
    }


def install(registry):
    for module in modules():
        registry.register_module(module)


def builtin_names():
    """Read literal plugin IDs without importing unselected implementations."""
    import ast
    from pathlib import Path

    result = {}
    for path in Path(__file__).parent.glob("*.py"):
        if path.name.startswith("_"):
            continue
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "ID" for t in node.targets
            ):
                result[ast.literal_eval(node.value)] = f"{__name__}.{path.stem}"
    return result
