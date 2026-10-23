"""The default catalog of installed single-capability plugins."""

from . import definition, modules

DEFAULTS = {"data_transfer": {"plugin": "buffered-transfer"}}


def catalog():
    providers = modules()
    return {
        "version": "1.0.0",
        "defaults": DEFAULTS,
        "plugins": [definition(m) for m in providers if m.CAPABILITY != "goal"],
        "runtime": {
            m.ID: definition(m)["capabilities"]["services"]
            for m in providers
            if getattr(m, "RUNTIME_DEFAULT", False)
        },
        "solver": {"plugin": "backward_chain"},
    }
