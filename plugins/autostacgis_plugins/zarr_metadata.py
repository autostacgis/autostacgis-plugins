"""Read Zarr metadata without loading the complete dataset."""

from autostacgis.encoding import embed


def metadata(record, settings, context):
    return embed(record, settings, context, "zarr")


ID = "zarr-metadata"
CAPABILITY = "metadata_out"
IMPLEMENTATION = metadata
REQUIRES = ()

VERSION = "0.0.1"
DEPENDENCIES = []
