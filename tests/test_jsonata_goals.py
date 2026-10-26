"""JSONata goal synthesis and AOI selection over bbox and polygon metadata."""

from copy import deepcopy

import pytest
from autostacgis import Application, Registry, module
from autostacgis.contracts import test as predicate
from autostacgis.errors import AutoSTACGISError, NoPlan
from autostacgis.expressions import evaluate
from autostacgis.goals import selected
from shapely.geometry import box, mapping
from test_solvers import scene
from workflow_helpers import configured


def application(tmp_path, *processes):
    registry = Registry(builtins=False)
    for name, process in processes:
        registry.register(name, "process", process, requires=getattr(process, "requires", ()))
    return Application(
        {
            "solver": {"backward_chain": {}},
            "goal": {"metadata-value": {"jsonata": "true", "value": True}},
            "process": {name: {} for name, _ in processes},
            "metadata_structure": {"strict": False},
        },
        registry=registry,
        base_dir=tmp_path,
    )


def request(expression, value, **settings):
    return {
        "goal": {"plugin": "metadata-value", "settings": {"jsonata": expression, "value": value, **settings}}
    }


def rectangle(name, extent):
    record = scene()
    record.item["id"] = name
    record.item["bbox"] = list(extent)
    record.item["geometry"] = dict(mapping(box(*extent)))
    record.key = name
    return record


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("item.properties.ready", True),
        ("$sum([1, 2, 3])", 6.0),
        ('{"ready": item.properties.ready, "values": [1, 2]}', {"ready": True, "values": [1, 2]}),
        ("kind", "raster"),
        ("asset_key", "data"),
        ("$lookup(asset, 'roles')", ["data"]),
    ],
)
def test_jsonata_can_solve_for_scalar_array_and_object_values(tmp_path, expression, expected):
    app = application(tmp_path)
    assert app.solver_name == "backward_chain"
    assert configured(app, request(expression, expected)).plan(inputs=[scene()]).steps == []


def test_unknown_values_and_boolean_number_mismatches_cannot_satisfy_goals(tmp_path):
    app = application(tmp_path)
    for expression, expected in [
        ("item.properties.missing", None),
        ("item.properties.missing", False),
        ("1", True),
        ("[1]", [True]),
    ]:
        with pytest.raises(NoPlan):
            configured(app, request(expression, expected)).plan(inputs=[scene()])


def test_jsonata_goal_is_regressed_through_multiple_processing_steps_and_executed(tmp_path):
    def step(field):
        @module(
            argument_requirements={
                "image": {"kind": "raster", "data_types": ["raster"], "require": {f"properties.{field}": 0}}
            },
            outputs={
                "result": {
                    "kind": "raster",
                    "data_types": ["raster"],
                    "inherit_metadata": ["image"],
                    "set": [{f"properties.{field}": 1}],
                }
            },
        )
        def process(image, settings, context):
            return {"result": [context.output("result", image.payload, facts={f"properties.{field}": 1})]}

        return process

    app = application(tmp_path, ("set-a", step("a")), ("set-b", step("b")))
    image = scene()
    image.item["properties"].update(a=0, b=0)
    goal = request(
        "$sum([item.properties.a, item.properties.b])", 2, observes=["properties.a", "properties.b"]
    )
    plan = configured(app, goal).plan(inputs=[image])
    assert {step.module for step in plan.steps} == {"set-a", "set-b"}
    assert plan.report["engine"] == "backward_chain"
    with configured(app, goal).run(inputs=[image]) as result:
        assert result.records[0].item["properties"]["a"] == result.records[0].item["properties"]["b"] == 1


@pytest.mark.parametrize("field", ["bbox", "geometry", "properties.valid_footprint"])
def test_aoi_gathers_only_intersecting_images_from_the_selected_metadata_field(tmp_path, field):
    app = application(tmp_path)
    images = [
        rectangle("west", [0, 0, 1, 1]),
        rectangle("east", [1, 0, 2, 1]),
        rectangle("distant", [10, 10, 11, 11]),
    ]
    if field == "properties.valid_footprint":
        for image in images:
            image.item["properties"]["valid_footprint"] = deepcopy(image.item["geometry"])
    goal = request(
        "item.properties.ready",
        True,
        parameters={"aoi": [0.25, 0, 1.75, 1]},
        select={"jsonata": f"$intersects(item.{field}, parameters.aoi)"},
        for_each=True,
    )
    plan = configured(app, goal).plan(inputs=images)
    assert len(plan.outputs) == 2
    with configured(app, goal).run(inputs=images) as result:
        assert {record.item["id"] for record in result} == {"west", "east"}


def test_polygon_selection_uses_the_polygon_instead_of_its_bbox(tmp_path):
    record = rectangle("triangle", [0, 0, 2, 2])
    record.item["geometry"] = {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [0, 2], [0, 0]]]}
    parameters = {"aoi": [1.5, 1.5, 1.8, 1.8]}
    assert (
        predicate(record, {"jsonata": "$intersects(item.bbox, parameters.aoi)", "parameters": parameters})
        is True
    )
    assert (
        predicate(record, {"jsonata": "$intersects(item.geometry, parameters.aoi)", "parameters": parameters})
        is False
    )
    record.item["geometry"] = None
    assert selected(record, {"bbox": parameters["aoi"]}) is True


def test_jsonata_coverage_goal_can_synthesize_an_aggregation_of_adjacent_images(tmp_path):
    @module(
        argument_requirements={
            "images": {
                "kind": "raster",
                "data_types": ["raster"],
                "cardinality": "many",
                "sequence": {"plugin": "gather-all"},
            }
        },
        outputs={
            "result": {
                "kind": "raster",
                "data_types": ["raster"],
                "inherit_metadata": ["images"],
                "geometry": "union",
            }
        },
    )
    def aggregate(inputs, settings, context):
        pytest.fail("Planning must not execute processing functions")

    aggregate.requires = ("gather-all",)
    app = application(tmp_path, ("aggregate", aggregate))
    images = [rectangle("west", [0, 0, 1, 1]), rectangle("east", [1, 0, 2, 1])]
    goal = request(
        "$covers(item.geometry, parameters.aoi)",
        True,
        parameters={"aoi": [0, 0, 2, 1]},
        observes=["geometry"],
    )
    plan = configured(app, goal).plan(inputs=images)
    assert [step.module for step in plan.steps] == ["aggregate"]
    result = plan.predicted[plan.outputs["result"][0]]
    assert (
        predicate(
            result, {"jsonata": "$covers(item.geometry, parameters.aoi)", "parameters": {"aoi": [0, 0, 2, 1]}}
        )
        is True
    )


def test_count_coverage_and_path_goal_parameters_remain_available(tmp_path):
    app = application(tmp_path)
    record = rectangle("full", [0, 0, 2, 2])
    record.item["properties"]["footprint"] = deepcopy(record.item["geometry"])
    for mode, extra in [("bbox", {}), ("footprint", {}), ("metadata", {"path": "properties.footprint"})]:
        goal = {
            "goal": {
                "plugin": "metadata-value",
                "settings": {
                    "path": "properties.ready",
                    "value": True,
                    "count": 1,
                    "coverage": {"geometry": [0.5, 0.5, 1.5, 1.5], "mode": mode, **extra},
                },
            }
        }
        assert configured(app, goal).plan(inputs=[record]).steps == []
    with pytest.raises(AutoSTACGISError):
        configured(app, request("true", True, for_each=True, count=2)).plan(inputs=[record])
    with pytest.raises(AutoSTACGISError):
        configured(app, request("true", True, path="properties.ready")).plan(inputs=[record])


def test_spatial_functions_handle_missing_invalid_antimeridian_and_3d_bbox_metadata():
    assert evaluate("$intersects(a, b)", {"a": [170, -10, -170, 10], "b": [175, -1, 179, 1]}) is True
    assert evaluate("$intersects(a, b)", {"a": [170, -10, -170, 10], "b": [-1, -1, 1, 1]}) is False
    assert evaluate("$covers(a, b)", {"a": [0, 0, 0, 2, 2, 10], "b": [0.5, 0.5, 1.5, 1.5]}) is True
    assert evaluate("$within(b, a)", {"a": [0, 0, 2, 2], "b": [0.5, 0.5, 1.5, 1.5]}) is True
    for invalid in (None, [], [0, 1, 2], {"type": "Unknown"}):
        assert evaluate("$intersects(a, b)", {"a": invalid, "b": [0, 0, 1, 1]}) is None
    with pytest.raises(AutoSTACGISError, match="time, randomness"):
        evaluate("$random()", {})
