def direct(app, settings, request):
    return app.run(request or settings["request"])


ID = "cli"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = direct
