"""Submit workflow execution to a configured Slurm cluster."""


def slurm(app, settings):
    """Submit an AutoSTACGIS invocation to an existing Slurm installation."""
    import json
    import shlex
    import subprocess
    from uuid import uuid4

    from autostacgis.errors import AutoSTACGISError

    directory = app.work / "slurm" / uuid4().hex
    directory.mkdir(parents=True)
    configuration = directory / "workflow.json"
    configuration.write_text(json.dumps(app.snapshot()))
    script = directory / "job.sh"
    code = 'from autostacgis import Application; from autostacgis.config import read; import sys; a=Application(read(sys.argv[1]),base_dir=sys.argv[2]); r=a.run(); r.close() if hasattr(r,"close") else None'
    command = [settings.get("python", "python"), "-c", code, str(configuration), str(app.base_dir)]
    script.write_text("#!/bin/sh\nset -eu\nexec " + shlex.join(command) + "\n")
    if settings.get("prepare_only", False):
        return str(script)
    options = settings.get("sbatch", {})
    allowed = {"partition", "account", "time", "cpus-per-task", "mem", "gres", "constraint", "job-name"}
    if set(options) - allowed:
        raise AutoSTACGISError("Unsupported sbatch option")
    result = subprocess.run(
        ["sbatch", "--parsable", *(f"--{key}={value}" for key, value in options.items()), str(script)],
        check=True,
        text=True,
        capture_output=True,
    )
    return {"job_id": result.stdout.strip(), "script": str(script)}


ID = "slurm"
REQUIRES = ()

CAPABILITY = "trigger"
IMPLEMENTATION = slurm

VERSION = "0.0.1"
DEPENDENCIES = []
