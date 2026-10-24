"""Check optical band compatibility between images."""


def compatible_optical(inputs, settings, context):
    """Bind bands from the same acquisition; processing may change their radiometry."""
    from autostacgis.contracts import value
    from autostacgis.metadata import MISSING

    # Pansharpening requires the same registration reference frame. Matching
    # CRS codes alone do not align a corrected MUL with an uncorrected PAN.
    frames = []
    for records in inputs.values():
        for record in records:
            history = value(record, "assets.$asset.data_state:registration")
            if history is MISSING or history is None:
                history = []
            if any(entry.get("target") is None for entry in history):
                return "unknown"
            frames.append(
                [
                    (
                        entry.get("kind"),
                        sorted(
                            str(target.get("uuid") or target.get("id") or target.get("href"))
                            for target in (entry.get("target") or [])
                        ),
                    )
                    for entry in history
                ]
            )
    if any(frame != frames[0] for frame in frames[1:]):
        return "fail"
    return context.call(
        "same-fields",
        "checks",
        inputs,
        {"fields": settings.get("fields", ["properties.platform", "properties.datetime"])},
    )


ID = "compatible-optical"
REQUIRES = ("same-fields",)

CAPABILITY = "checks"
IMPLEMENTATION = compatible_optical

VERSION = "1.1.1"
DEPENDENCIES = []
