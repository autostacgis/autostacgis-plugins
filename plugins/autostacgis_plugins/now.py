"""Run the workflow immediately in the current application."""


def direct(app, settings, request):
    return app.run(request or app.request())


ID = "now"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = direct

VERSION = "1.1.1"
DEPENDENCIES = []
