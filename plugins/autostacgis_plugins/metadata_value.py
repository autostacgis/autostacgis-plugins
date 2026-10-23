"""Build JSONata or direct-path metadata goals for backward chaining."""

from copy import deepcopy

from .backward_chain import BackwardChainSolver


def _parameters(value, parameters):
    if isinstance(value, list):
        return [_parameters(child, parameters) for child in value]
    if not isinstance(value, dict):
        return value
    result = deepcopy(value)
    for key in ("require", "metadata", "all", "any", "not"):
        if key in result:
            result[key] = _parameters(result[key], parameters)
    if "jsonata" in result:
        result["parameters"] = {**parameters, **result.get("parameters", {})}
    return result


def metadata_value(settings, records, context):
    specification = {
        field: deepcopy(settings[field])
        for field in ("name", "kind", "select", "count", "coverage", "publish")
        if field in settings
    }
    if "jsonata" in settings:
        requirement = {"jsonata": settings["jsonata"], "equals": settings["value"]}
        for field in ("parameters", "observes"):
            if field in settings:
                requirement[field] = deepcopy(settings[field])
    else:
        requirement = {"path": settings["path"], "equals": settings["value"]}
    specification["require"] = requirement
    if "select" in specification:
        specification["select"] = _parameters(specification["select"], settings.get("parameters", {}))
    return {"for_each" if settings.get("for_each", False) else "output": specification}


_output = next(
    form["properties"]["output"]
    for form in BackwardChainSolver.contract["goal_schema"]["$defs"]["goal"]["oneOf"]
    if "output" in form.get("properties", {})
)
metadata_value.contract = {
    "solver": "backward_chain",
    "settings_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "minLength": 1,
                "description": "Direct metadata path, including optional $asset binding.",
            },
            "jsonata": {
                "type": "string",
                "minLength": 1,
                "description": "Pure JSONata over item, asset, asset_key, kind, and parameters.",
            },
            "value": {
                "description": "Expected JSONata result or direct metadata value; null remains unknown."
            },
            "parameters": {
                "type": "object",
                "description": "JSON constants available to goal and selection expressions as parameters.",
            },
            "observes": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
                "uniqueItems": True,
                "description": "Optional complete list of metadata paths read by the goal expression; omitted means all metadata.",
            },
            "name": {"type": "string", "minLength": 1},
            "kind": {"type": "string", "minLength": 1},
            "select": {
                "type": "object",
                "description": "Initial source selection, including JSONata and AOI predicates.",
            },
            "for_each": {"type": "boolean", "default": False},
            **{field: deepcopy(_output["properties"][field]) for field in ("count", "coverage", "publish")},
        },
        "required": ["value"],
        "oneOf": [
            {"required": ["path"], "not": {"required": ["jsonata"]}},
            {"required": ["jsonata"], "not": {"required": ["path"]}},
        ],
        "allOf": [
            {
                "if": {"required": ["for_each"], "properties": {"for_each": {"const": True}}},
                "then": {"not": {"required": ["count"]}},
            }
        ],
        "dependentRequired": {"observes": ["jsonata"]},
        "additionalProperties": False,
    },
}

ID = "metadata-value"
CAPABILITY = "goal"
IMPLEMENTATION = metadata_value
REQUIRES = ("backward_chain",)

VERSION = "1.0.0"
DEPENDENCIES = []
