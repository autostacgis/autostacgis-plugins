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


def boolean_registry(*names):
    registry = Registry(builtins=False)
    for name in names:
        registry.register(name, "solver", BooleanSolver)
    return registry


def test_generic_metadata_goal_loads_its_solver_and_runs(tmp_path):
    app = Application({"version": "1.0.0", "plugins": [{"use": "metadata-value"}]}, base_dir=tmp_path)
    request = {"goal": {"plugin": "metadata-value", "settings": {"path": "properties.ready", "value": True}}}
    # Execution services are ordinary named dependencies, independently selected.
    app = Application(
        {
            "catalog": {
                "version": "1.0.0",
                "plugins": [{"use": name} for name in ("metadata-value", "executor", "storage", "events")],
            },
            "request": request,
        },
        base_dir=tmp_path,
    )
    assert app.solver_name == "backward_chain"
    assert app.registry.requirements["metadata-value"] == ("backward_chain",)
    assert app.plan(inputs=[scene()]).steps == []
    with app.run(inputs=[scene()]) as result:
        assert result.records[0].item["properties"]["ready"] is True
    assert app.available(inputs=[scene()])["requested"]["status"] == "synthesized"


def test_metadata_goal_requires_all_declared_parameters_and_rejects_unknown_ones():
    app = Application({"version": "1.0.0", "plugins": [{"use": "metadata-value"}]})
    for settings in ({"path": "properties.ready"}, {"path": "properties.ready", "value": True, "typo": 1}):
        with pytest.raises(AutoSTACGISError, match="metadata-value"):
            app.plan({"goal": {"plugin": "metadata-value", "settings": settings}}, [scene()])


@pytest.mark.parametrize(
    "settings", [{"timeout": 0}, {"max_steps": -1}, {"max_states": 1.5}, {"max_bindings": 0}, {"typo": 1}]
)
def test_solver_parameters_use_the_installed_contract(settings):
    with pytest.raises(AutoSTACGISError, match="backward_chain"):
        Application({"version": "1.0.0", "plugins": [{"use": "backward_chain", "settings": settings}]})
    app = Application()
    with pytest.raises(AutoSTACGISError, match="backward_chain"):
        app.plan(
            {"goal": {"output": {}}, "solver": {"plugin": "backward_chain", "settings": settings}}, [scene()]
        )


def test_solver_contract_and_effective_parameters_are_explicit():
    app = Application(
        {
            "version": "1.0.0",
            "plugins": [{"use": "backward_chain", "settings": {"timeout": 45}}],
            "solver": {"plugin": "backward_chain", "settings": {"max_steps": 8}},
        }
    )
    settings = app.solver_settings({"solver": {"plugin": "backward_chain", "settings": {"timeout": 10}}})
    assert settings == {"max_steps": 8, "max_states": 100000, "max_bindings": 100000, "timeout": 10}
    definition = app.registry.definition("backward_chain")["capabilities"]["solver"]
    assert set(definition["contract"]["settings_schema"]["properties"]) == set(settings)
    assert "goal_schema" in definition["contract"]


def test_two_selected_solvers_are_rejected_even_with_a_selector():
    registry = boolean_registry("one", "two")
    for selector in (None, {"plugin": "one"}):
        catalog = {"version": "1.0.0", "plugins": [{"use": "one"}, {"use": "two"}]}
        if selector:
            catalog["solver"] = selector
        with pytest.raises(AutoSTACGISError, match="Exactly one solver"):
            Application(catalog, registry=registry)


def test_unused_registered_solver_is_not_selected():
    registry = boolean_registry("one", "two")
    app = Application({"version": "1.0.0", "plugins": [{"use": "one"}]}, registry=registry)
    assert app.solver_name == "one"
    assert "two" not in app.plugins
    assert "backward_chain" not in app.plugins
    assert app.plan({"goal": {"accept": True}}, [scene()]).report["engine"] == "boolean"
    with pytest.raises(AutoSTACGISError, match="Only solver one is active"):
        app.plan({"goal": {"accept": True}, "solver": {"plugin": "two"}}, [scene()])


def test_custom_solver_owns_goal_syntax_and_live_output_validation(tmp_path):
    registry = boolean_registry("boolean")
    app = Application(
        {
            "version": "1.0.0",
            "plugins": [{"use": name} for name in ("boolean", "executor", "storage", "events")],
        },
        registry=registry,
        base_dir=tmp_path,
    )
    with app.run({"goal": {"accept": True}}, [scene()]) as result:
        assert result.plan.report["engine"] == "boolean"
    with pytest.raises(AutoSTACGISError, match="Actual outputs"):
        app.run({"goal": {"accept": False}}, [scene()])
    with pytest.raises(AutoSTACGISError, match="boolean goal"):
        app.plan({"goal": {"output": {}}}, [scene()])


def test_goal_dependency_uses_the_same_named_requirement_as_other_plugins():
    def goal(settings, records, context):
        return {"accept": settings["accept"]}

    goal.contract = {
        "solver": "boolean",
        "settings_schema": {
            "type": "object",
            "properties": {"accept": {"type": "boolean"}},
            "required": ["accept"],
            "additionalProperties": False,
        },
    }
    registry = boolean_registry("boolean")
    with pytest.raises(AutoSTACGISError, match="name its solver in REQUIRES"):
        registry.register("bad-goal", "goal", goal)
    registry.register("boolean-goal", "goal", goal, requires=("boolean",))
    app = Application({"version": "1.0.0", "plugins": [{"use": "boolean-goal"}]}, registry=registry)
    assert app.solver_name == "boolean"
    assert app.plan({"goal": {"plugin": "boolean-goal", "settings": {"accept": True}}}, [scene()]).steps == []


def test_solver_goal_mismatch_and_missing_dependency_fail_before_search():
    registry = boolean_registry("boolean")
    with pytest.raises(AutoSTACGISError, match="Exactly one solver"):
        Application(
            {"version": "1.0.0", "plugins": [{"use": "boolean"}, {"use": "metadata-value"}]},
            registry=registry,
        )
    from autostacgis_plugins.metadata_value import metadata_value

    registry.register("unavailable-goal", "goal", metadata_value, requires=("backward_chain",))
    definition = registry.definition("unavailable-goal")
    with pytest.raises(AutoSTACGISError, match="unavailable: backward_chain"):
        Application(
            {"version": "1.0.0", "plugins": [registry.definition("boolean"), definition]}, registry=registry
        )


def test_goal_adapter_output_is_checked_against_its_solver_contract():
    def invalid(settings, records, context):
        return {"not_a_metadata_goal": {}}

    invalid.contract = {"solver": "backward_chain", "settings_schema": EMPTY_SETTINGS}
    registry = Registry(builtins=False)
    registry.register("invalid", "goal", invalid, requires=("backward_chain",))
    app = Application({"version": "1.0.0", "plugins": [{"use": "invalid"}]}, registry=registry)
    with pytest.raises(AutoSTACGISError, match="backward_chain goal"):
        app.plan({"goal": {"plugin": "invalid"}}, [scene()])


def test_catalog_cannot_replace_an_installed_solver_contract():
    registry = Registry()
    definition = registry.definition("backward_chain")
    definition["capabilities"]["solver"]["contract"]["settings_schema"]["additionalProperties"] = True
    with pytest.raises(AutoSTACGISError, match="cannot be overridden"):
        Application({"version": "1.0.0", "plugins": [definition]}, registry=registry)


def test_duplicate_names_and_entry_point_aliases_are_rejected(monkeypatch):
    registry = Registry(builtins=False)
    registry.register("unique", "checks", lambda: None)
    with pytest.raises(AutoSTACGISError, match="Duplicate"):
        registry.register("unique", "checks", lambda: None)
    import autostacgis.registry as registry_module

    provider = SimpleNamespace(
        ID="canonical", VERSION="1.0.0", CAPABILITY="checks", IMPLEMENTATION=lambda: None, REQUIRES=()
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


@pytest.mark.parametrize(
    "goal",
    [
        {"plugin": []},
        {"plugin": "metadata-value", "settings": []},
        {"all_of": {}},
        {"any_of": []},
    ],
)
def test_invalid_goal_parameter_shapes_fail_as_configuration_errors(goal):
    app = Application({"version": "1.0.0", "plugins": [{"use": "metadata-value"}]})
    with pytest.raises(AutoSTACGISError):
        app.plan({"goal": goal}, [scene()])


def test_default_providers_load_their_named_dependencies():
    class Transfer:
        input_types = ["bytes"]
        output_types = ["bytes"]

    registry = Registry(builtins=False)
    registry.register("transfer", "data_transfer", Transfer, requires=("storage",))
    app = Application(
        {"version": "1.0.0", "plugins": [], "defaults": {"data_transfer": {"plugin": "transfer"}}},
        registry=registry,
    )
    assert {"transfer", "storage", "backward_chain"} <= set(app.plugins)
