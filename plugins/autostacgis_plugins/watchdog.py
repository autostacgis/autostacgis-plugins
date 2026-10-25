"""Run workflows in response to watchdog filesystem events."""

from autostacgis.triggers import file_trigger


def watchdog(app, settings, request):
    return file_trigger(app, settings, request)


watchdog.settings_schema = file_trigger.settings_schema

ID = "watchdog"
CAPABILITY = "trigger"
IMPLEMENTATION = watchdog
REQUIRES = ()

VERSION = "0.0.1"
DEPENDENCIES = ["watchdog>=6,<7"]
