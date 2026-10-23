from autostacgis.triggers import timed_trigger


def apscheduler(app, settings, request):
    return timed_trigger(app, settings, request)


apscheduler.settings_schema = timed_trigger.settings_schema

ID = "apscheduler"
CAPABILITY = "trigger"
IMPLEMENTATION = apscheduler
REQUIRES = ()

VERSION = "1.0.0"
DEPENDENCIES = ["APScheduler>=3.11,<4"]
