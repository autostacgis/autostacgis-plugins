"""Partition a collection into independently bound processing groups."""

from autostacgis.errors import AutoSTACGISError
from autostacgis.sequence import Group


def split(records, settings, context):
    size = settings.get("size", 1)
    if type(size) is not int or size < 1:
        raise AutoSTACGISError("split.size must be a positive integer")
    return [Group(records[i : i + size]) for i in range(0, len(records), size)]


ID = "split"
REQUIRES = ()
DEFAULTS = {"size": 1}

CAPABILITY = "sequence"
IMPLEMENTATION = split

VERSION = "0.0.1"
DEPENDENCIES = []
