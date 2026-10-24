"""Gather all available records into one processing group."""

from autostacgis.sequence import Group


def gather_all(records, settings, context):
    return [Group(records)] if records else []


ID = "gather-all"
REQUIRES = ()

CAPABILITY = "sequence"
IMPLEMENTATION = gather_all

VERSION = "1.1.0"
DEPENDENCIES = []
