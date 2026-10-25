"""Read GeoTIFF raster dimensions, bands, and georeferencing."""

from autostacgis.encoding import embed


def metadata(record, settings, context):
    return embed(record, settings, context, "geotiff")


ID = "geotiff-metadata"
CAPABILITY = "metadata_out"
IMPLEMENTATION = metadata
REQUIRES = ()

VERSION = "0.0.1"
DEPENDENCIES = []
