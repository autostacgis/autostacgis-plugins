"""Invoke workflows through an explicitly configured command-line trigger."""


def direct(app, settings):
    return app.run()


ID = "cli"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = direct

VERSION = "0.0.1"
DEPENDENCIES = []
