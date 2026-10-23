"""Discover self-contained plugin modules."""

from copy import deepcopy
from importlib import import_module
from pkgutil import iter_modules


def modules():
    return sorted(
        (import_module(f"{__name__}.{e.name}") for e in iter_modules(__path__) if not e.name.startswith("_")),
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
