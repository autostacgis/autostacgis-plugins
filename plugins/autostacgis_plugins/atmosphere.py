"""Discover atmospheric auxiliary data for radiometric correction."""

from datetime import datetime

from autostacgis.ancillary import descriptor


class AtmosphereSource:
    """NASA POWER daily atmosphere samples; missing physical quantities stay unknown."""

    def discover(self, settings, query, app):
        yield descriptor(settings, query, "atmosphere", "table")

    def discover_from(self, settings, query, app, records):
        scenes = [
            r
            for r in records
            if r.kind == "raster"
            and r.item.get("properties", {}).get("datetime")
            and any(a.get("data_state:modality") == "optical" for a in r.item.get("assets", {}).values())
        ]
        if not scenes:
            yield from self.discover(settings, query, app)
            return
        seen = set()
        for scene in scenes:
            acquired = scene.item["properties"]["datetime"]
            day = datetime.fromisoformat(acquired.replace("Z", "+00:00")).date().isoformat()
            bounds = scene.item.get("bbox")
            if not bounds:
                continue
            key = (day, tuple(bounds))
            if key in seen:
                continue
            seen.add(key)
            yield descriptor(
                settings,
                {"area": bounds, "time_range": [day + "T00:00:00Z", day + "T23:59:59Z"]},
                "atmosphere",
                "table",
            )


ID = "atmosphere"
REQUIRES = ("atmosphere-download",)


AtmosphereSource.data_in = "atmosphere-download"

CAPABILITY = "metadata_in"
IMPLEMENTATION = AtmosphereSource

VERSION = "1.1.0"
DEPENDENCIES = []
