"""Validate STAC metadata against a configured JSON Schema."""


def metadata_schema(inputs, settings, context):
    from jsonschema import ValidationError

    try:
        for records in inputs.values():
            for record in records:
                context.stac.validate_schema(record.item, settings["schema"])
    except ValidationError:
        return "fail"
    return "pass"


ID = "metadata-schema"
REQUIRES = ()

CAPABILITY = "checks"
IMPLEMENTATION = metadata_schema

VERSION = "0.0.1"
DEPENDENCIES = []
