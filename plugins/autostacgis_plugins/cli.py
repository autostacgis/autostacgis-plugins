"""Invoke workflows through an explicitly configured command-line trigger."""


def direct(app, settings, request):
    return app.run(request or settings["request"])


ID = "cli"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = direct

VERSION = "0.0.1"
DEPENDENCIES = []
