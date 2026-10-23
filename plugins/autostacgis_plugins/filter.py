from autostacgis.metadata import matches
from autostacgis.sequence import Group


def filtered(records, settings, context):
    selected = [r for r in records if matches(r.item, settings.get("equals", {})) == "pass"]
    return [Group(selected)] if selected else []


ID = "filter"
REQUIRES = ()


CAPABILITY = "sequence"
IMPLEMENTATION = filtered

VERSION = "1.0.0"
DEPENDENCIES = []
