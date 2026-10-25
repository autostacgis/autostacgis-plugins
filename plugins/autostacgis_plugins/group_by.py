"""Group records by configured metadata fields."""

from collections import defaultdict

from autostacgis.errors import AutoSTACGISError
from autostacgis.metadata import MISSING, get
from autostacgis.model import digest
from autostacgis.sequence import Group


def group_by(records, settings, context):
    groups = defaultdict(list)
    for record in records:
        value = get(record.item, settings["field"])
        if value is MISSING or value is None:
            raise AutoSTACGISError(f"Missing grouping field {settings['field']} on {record.key}")
        groups[digest(value)].append(record)
    return [Group(groups[k]) for k in sorted(groups)]


ID = "group-by"
REQUIRES = ()

CAPABILITY = "sequence"
IMPLEMENTATION = group_by

VERSION = "0.0.1"
DEPENDENCIES = []
