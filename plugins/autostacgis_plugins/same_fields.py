"""Check that records share the required metadata field values."""

from autostacgis.checks import combine
from autostacgis.contracts import value
from autostacgis.metadata import MISSING


def same_fields(inputs, settings, context):
    records = [r for group in inputs.values() for r in group]
    result = []
    for field in settings["fields"]:
        values = [value(r, field) for r in records]
        if any(v is MISSING or v is None for v in values):
            result.append("unknown")
        else:
            result.append("pass" if all(v == values[0] for v in values) else "fail")
    return combine(result)


ID = "same-fields"
REQUIRES = ()

CAPABILITY = "checks"
IMPLEMENTATION = same_fields

VERSION = "1.1.0"
DEPENDENCIES = []
