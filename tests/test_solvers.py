"""Solver selection, solver-specific goals, execution, and shared named dependencies."""

from types import SimpleNamespace

import numpy as np
import pytest
from autostacgis import Application, Record, Registry
from autostacgis.data import ArrayRaster, Grid
from autostacgis.errors import AutoSTACGISError
from autostacgis.model import Plan

EMPTY_SETTINGS = {"type": "object", "properties": {}, "additionalProperties": False}


def scene():
    item = {
        "type": "Feature",
        "stac_version": "1.1.0",
        "id": "scene",
        "geometry": None,
        "properties": {"datetime": "2026-01-01T00:00:00Z", "ready": True},
        "links": [],
        "assets": {"data": {"href": "memory://scene", "roles": ["data"]}},
    }
    grid = Grid(2, 2, 1, "float32", (1, 0, 0, 0, -1, 2), "EPSG:4326")
    return Record(item, payload=ArrayRaster(np.ones(grid.shape, dtype="float32"), grid))


class BooleanSolver:
    contract = {
        "settings_schema": EMPTY_SETTINGS,
        "goal_schema": {
            "type": "object",
            "properties": {"accept": {"type": "boolean"}},
            "required": ["accept"],
            "additionalProperties": False,
        },
    }

    def __init__(self, app, request, settings):
        self.accept = request["goal"]["accept"]

    def plan(self, records):
        records = [record.clone() for record in records]
        for record in records:
            record.runtime["origin"] = record.key
        initial = {record.key: record for record in records}
        return Plan([], initial, initial, {"result": list(initial)}, 0, report={"engine": "boolean"})

    def validate_outputs(self, plan, records):
        return self.accept


def workflow(settings=None, **sections):
    return {
        "solver": {"backward_chain": {}},
        "goal": {"metadata-value": settings or {"path": "properties.ready", "value": True}},
        "metadata_structure": {"strict": False},
        **sections,
    }


def boolean_registry(*names):
    registry = Registry(builtins=False)
    for name in names:
        registry.register(name, "solver", BooleanSolver)

        def goal(settings, records, context):
            return {"accept": settings["accept"]}

        goal.contract = {"solver": name, "settings_schema": BooleanSolver.contract["goal_schema"]}
        registry.register(name + "-goal", "goal", goal, requires=(name,))
    return registry


def boolean_workflow(name="boolean", accept=True):
    return workflow(solver={name: {}}, goal={name + "-goal": {"accept": accept}})


def test_generic_metadata_goal_loads_its_solver_and_runs(tmp_path):
    app = Application(workflow(), base_dir=tmp_path)
    assert app.solver_name == "backward_chain"
    assert app.registry.requirements["metadata-value"] == ("backward_chain",)
    assert app.plan(inputs=[scene()]).steps == []
    with app.run(inputs=[scene()]) as result:
        assert result.records[0].item["properties"]["ready"] is True
    assert app.available(inputs=[scene()])["requested"]["status"] == "synthesized"


def test_metadata_goal_requires_all_declared_parameters_and_rejects_unknown_ones():
    for settings in ({"path": "properties.ready"}, {"path": "properties.ready", "value": True, "typo": 1}):
        with pytest.raises(AutoSTACGISError, match="metadata-value"):
            Application(workflow(settings))


@pytest.mark.parametrize(
    "settings", [{"timeout": 0}, {"max_steps": -1}, {"max_states": 1.5}, {"max_bindings": 0}, {"typo": 1}]
)
def test_solver_parameters_use_the_installed_contract(settings):
    with pytest.raises(AutoSTACGISError, match="backward_chain"):
        Application(workflow(solver={"backward_chain": settings}))


def test_solver_contract_and_effective_parameters_are_explicit():
    app = Application(workflow(solver={"backward_chain": {"max_steps": 8, "timeout": 45}}))
    settings = app.solver_settings()
    assert settings == {"max_steps": 8, "max_states": 100000, "max_bindings": 100000, "timeout": 45}
    definition = app.registry.definition("backward_chain")["capabilities"]["solver"]
    assert set(definition["contract"]["settings_schema"]["properties"]) == set(settings)
    assert "goal_schema" in definition["contract"]


def test_two_selected_solvers_are_rejected():
    with pytest.raises(AutoSTACGISError):
        Application(
            boolean_workflow("one") | {"solver": {"one": {}, "two": {}}},
            registry=boolean_registry("one", "two"),
        )


def test_unused_registered_solver_is_not_selected():
    app = Application(boolean_workflow("one"), registry=boolean_registry("one", "two"))
    assert app.solver_name == "one"
    assert "two" not in app.plugins
    assert "backward_chain" not in app.plugins
    assert app.plan(inputs=[scene()]).report["engine"] == "boolean"


def test_custom_solver_owns_goal_syntax_and_live_output_validation(tmp_path):
    registry = boolean_registry("boolean")
    with Application(boolean_workflow(), registry=registry, base_dir=tmp_path).run(
        inputs=[scene()]
    ) as result:
        assert result.plan.report["engine"] == "boolean"
    with pytest.raises(AutoSTACGISError, match="Actual outputs"):
        Application(boolean_workflow(accept=False), registry=registry, base_dir=tmp_path).run(
            inputs=[scene()]
        )
    with pytest.raises(AutoSTACGISError, match="boolean-goal"):
        Application(boolean_workflow() | {"goal": {"boolean-goal": {"output": {}}}}, registry=registry)


def test_goal_dependency_uses_the_same_named_requirement_as_other_plugins():
    registry = boolean_registry("boolean")
    goal = registry.resolve("goal", "boolean-goal")
    with pytest.raises(AutoSTACGISError, match="name its solver in REQUIRES"):
        registry.register("bad-goal", "goal", goal)
    app = Application(boolean_workflow(), registry=registry)
    assert app.registry.requirements["boolean-goal"] == ("boolean",)
    assert app.plan(inputs=[scene()]).steps == []


def test_goal_solver_mismatch_fails_before_search():
    with pytest.raises(AutoSTACGISError):
        Application(workflow(solver={"boolean": {}}), registry=boolean_registry("boolean"))


def test_goal_adapter_output_is_checked_against_its_solver_contract():
    def invalid(settings, records, context):
        return {"not_a_metadata_goal": {}}

    invalid.contract = {"solver": "backward_chain", "settings_schema": EMPTY_SETTINGS}
    registry = Registry(builtins=False)
    registry.register("invalid", "goal", invalid, requires=("backward_chain",))
    app = Application(workflow(goal={"invalid": {}}), registry=registry)
    with pytest.raises(AutoSTACGISError, match="backward_chain goal"):
        app.plan(inputs=[scene()])


def test_configuration_cannot_replace_an_installed_contract():
    document = workflow(solver={"backward_chain": {"contract": {}}})
    with pytest.raises(AutoSTACGISError, match="backward_chain"):
        Application(document)


def test_duplicate_names_and_entry_point_aliases_are_rejected(monkeypatch):
    registry = Registry(builtins=False)
    registry.register("unique", "checks", lambda: None)
    with pytest.raises(AutoSTACGISError, match="Duplicate"):
        registry.register("unique", "checks", lambda: None)
    import autostacgis.registry as registry_module

    provider = SimpleNamespace(
        ID="canonical", VERSION="0.0.1", CAPABILITY="checks", IMPLEMENTATION=lambda: None, REQUIRES=()
    )
    monkeypatch.setattr(
        registry_module,
        "entry_points",
        lambda **kwargs: [SimpleNamespace(name="alias", load=lambda: provider)],
    )
    with pytest.raises(AutoSTACGISError, match="unique plugin ID canonical"):
        Registry(builtins=False).load("alias")
    monkeypatch.setattr(
        registry_module,
        "entry_points",
        lambda **kwargs: [SimpleNamespace(name="storage", value="other.storage")],
    )
    with pytest.raises(AutoSTACGISError, match="Duplicate plugin name: storage"):
        Registry()


@pytest.mark.parametrize(
    "contract",
    [
        {},
        {"settings_schema": {"type": "object", "properties": {}}},
        {"settings_schema": EMPTY_SETTINGS, "goal_schema": {}},
        {
            "settings_schema": {**EMPTY_SETTINGS, "required": ["undeclared"]},
            "goal_schema": BooleanSolver.contract["goal_schema"],
        },
        {
            "settings_schema": EMPTY_SETTINGS,
            "settings": {"typo": 1},
            "goal_schema": BooleanSolver.contract["goal_schema"],
        },
    ],
)
def test_solver_registration_requires_explicit_valid_parameter_contracts(contract):
    class Invalid:
        pass

    Invalid.contract = contract
    with pytest.raises(AutoSTACGISError):
        Registry(builtins=False).register("invalid", "solver", Invalid)


@pytest.mark.parametrize("settings", [[], {"all_of": {}}, {"any_of": []}, {"plugin": []}])
def test_invalid_goal_parameter_shapes_fail_as_configuration_errors(settings):
    with pytest.raises(AutoSTACGISError):
        Application(workflow(goal={"metadata-value": settings}))


def test_default_providers_load_their_named_dependencies():
    class Transfer:
        input_types = ["bytes"]
        output_types = ["bytes"]

    registry = Registry(builtins=False)
    registry.register("transfer", "data_transfer", Transfer, requires=("storage",))
    app = Application(
        workflow(data_transfer={"transfer": {}}, execution={"data_transfer": {"plugin": "transfer"}}),
        registry=registry,
    )
    assert {"transfer", "storage", "backward_chain"} <= set(app.plugins)
