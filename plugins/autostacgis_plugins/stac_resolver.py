"""Discover ordinary local files and their sidecars as complete planning records."""

from autostacgis.local_discovery import LocalFiles
from autostacgis.raster_metadata import inspect_raster


class LocalStac:
    def discover(self, settings, query, context):
        from autostacgis.metadata import MISSING, get
        from jsonschema import ValidationError

        for record in LocalFiles().discover(settings, query, context):
            try:
                context.stac.validate(record.item)
                complete = all(
                    get(record.item, field) not in (MISSING, None)
                    for field in settings.get("required_fields", [])
                )
            except ValidationError:
                complete = False
            if not complete:
                record = inspect_raster(record, settings, context)
            yield record


ID = "stac-resolver"
REQUIRES = ()
DEFAULTS = {"search_glob": "data/*.tif"}

CAPABILITY = "metadata_in"
IMPLEMENTATION = LocalStac

VERSION = "0.0.1"
DEPENDENCIES = []
