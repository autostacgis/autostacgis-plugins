def direct(app, settings, request):
    return app.run(request or settings["request"])


ID = "python"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = direct
