"""Run the workflow immediately in the current application."""


def direct(app, settings):
    return app.run()


ID = "now"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = direct

VERSION = "0.0.1"
DEPENDENCIES = []
