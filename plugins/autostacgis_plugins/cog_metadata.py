from autostacgis.encoding import embed


def metadata(record, settings, context):
    return embed(record, settings, context, "cog")


ID = "cog-metadata"
CAPABILITY = "metadata_out"
IMPLEMENTATION = metadata
REQUIRES = ()

VERSION = "1.0.0"
DEPENDENCIES = []
