"""Build canonical workflow fixtures for solver execution tests."""


def configured(app, parameters):
    """Build a grouped workflow for a solver's unit-test execution parameters."""
    from copy import deepcopy

    from autostacgis import Application

    document = app.snapshot()
    parameters = deepcopy(parameters)
    parameters.pop("version", None)
    goal = parameters.pop("goal")
    if "plugin" in goal:
        document["goal"] = {goal["plugin"]: goal.get("settings", {})}
    else:
        test_goal = SolverGoal(app.solver_name, app.solver_implementation.contract["goal_schema"])
        if "test-goal" not in app.registry.plugins:
            app.registry.register("test-goal", "goal", test_goal, requires=(app.solver_name,))
        document["goal"] = {"test-goal": {"value": goal}}
    if "modules" in parameters:
        if "steps" not in parameters:
            document.setdefault("execution", {}).pop("steps", None)
        document["process"] = {
            name: document.get("process", {}).get(name, {}) for name in parameters["modules"]
        }
    for name, settings in parameters.pop("module_settings", {}).items():
        document.setdefault("process", {}).setdefault(name, {}).update(settings)
    for name, definition in parameters.pop("runtime", {}).items():
        settings = deepcopy(definition.get("settings", {}))
        if definition.get("implementation", name) != name:
            settings["backend"] = definition["implementation"]
        document.setdefault("services", {})[name] = settings
    if "solver" in parameters:
        call = parameters.pop("solver")
        document["solver"] = {call["plugin"]: call.get("settings", {})}
    document.setdefault("execution", {}).update(parameters)
    return Application(document, registry=app.registry, base_dir=app.base_dir, events=app.events)


class SolverGoal:
    """Serializable goal fixture exposing a solver's native contract."""

    def __init__(self, solver, schema):
        self.contract = {
            "solver": solver,
            "settings_schema": {
                "type": "object",
                "$defs": schema.get("$defs", {}),
                "properties": {"value": schema},
                "required": ["value"],
                "additionalProperties": False,
            },
        }

    def __call__(self, settings, records, context):
        return settings["value"]
