# Solver and goal contracts

A workflow selects exactly one solver under `solver`. Goal plugins name their required solver. Registered solvers may coexist; selecting two, including through goal dependencies, is an error. All settings come from the single workflow.

```yaml
solver:
  backward_chain:
    max_steps: 64
    max_states: 100000
    max_bindings: 100000
    timeout: 30
goal:
  metadata-value:
    path: assets.$asset.cf:standard_name
    value: surface_bidirectional_reflectance
    kind: raster
    for_each: true
    select:
      require:
        assets.$asset.data_state:spectral_sampling: multispectral
process:
  atmospheric_correction: {}
```

`backward_chain` constructs workflows backward from required outputs, memoizes subproblems, and regresses metadata predicates through declared processing effects. Metadata goals are inputs to this algorithm. It supports `output`, `for_each`, `all_of`, and `any_of`, including named outputs, source selection, counts, metadata predicates and spatial coverage. This syntax is declared in its `goal_schema`. The workflow selects goal adapters and their parameters; returned goals are validated against the selected solver dialect. Other goal adapters can target this solver, and other solvers can declare their own goal dialects.

## JSONata metadata values and areas of interest

`metadata-value` requires `value` and exactly one of `path` or `jsonata`. JSONata can compute a string, number, boolean, array, or object to compare with `value`. Expressions receive `item` (the STAC Item), `asset` (the bound asset), `asset_key`, `kind`, and JSON constants in `parameters`. Missing or null results remain unknown and cannot satisfy a goal. Boolean and numeric values are distinct.

This [workflow fragment](../examples/goals/jsonata-aoi.yaml) selects images intersecting an AOI and requests surface reflectance for every selected image:

```yaml
solver:
  backward_chain: {}
goal:
  metadata-value:
    jsonata: $lookup(asset, "cf:standard_name")
    value: surface_bidirectional_reflectance
    observes:
    - assets.$asset.cf:standard_name
    kind: raster
    for_each: true
    parameters:
      aoi:
      - -156.5
      - 20.5
      - -156.0
      - 21.0
    select:
      kind: raster
      require:
        jsonata: $intersects(item.bbox, parameters.aoi)
```

Select `metadata-value` and the necessary processing plugins in the workflow. `parameters` is shared with selection expressions; a selector's own parameters override matching names. `observes`, when supplied, must list every metadata path read by the goal expression. Omitting it conservatively considers all metadata when finding producers.

Spatial expressions accept GeoJSON geometries or Features and STAC bounding boxes:

| Expression | Meaning |
| --- | --- |
| `$intersects(item.bbox, parameters.aoi)` | Gather images whose bounding boxes touch or overlap the AOI |
| `$intersects(item.geometry, parameters.aoi)` | Gather images using their actual footprints |
| `$intersects(item.properties.valid_footprint, parameters.aoi)` | Gather images using another declared geometry field |
| `$covers(item.geometry, parameters.aoi)` | Require one output footprint to cover the whole AOI |
| `$within(item.geometry, parameters.aoi)` | Require the output footprint to lie within the AOI |

Both operands must use the same coordinate system; STAC geometry and bbox use WGS84 longitude/latitude. Four- and six-number STAC bounding boxes are supported; elevation is ignored for spatial comparisons. Bounding boxes crossing the antimeridian are split at ±180°. Invalid, empty, or missing geometry remains unknown. Polygon tests use the polygon itself, rather than its bounding box.

Selection filters the discovered inventory. Use the source provider's query settings to restrict remote discovery as well. `for_each: true` requests a separate result for each selected image. An `output` goal with source selection requires ancestry from every selected image, allowing a suitable aggregation. A [JSONata coverage goal](../examples/goals/jsonata-coverage.yaml) can request an output covering the AOI and synthesize an aggregation when a selected processing plugin declares the combined geometry.

Direct `path` equality remains available. Optional settings are `name`, `kind`, `select`, `for_each`, `parameters`, `observes`, `count` and `coverage`. `observes` requires `jsonata`; `count` is only available when `for_each` is false. Native `coverage` accepts `geometry` as GeoJSON or a four-number bbox and mode `footprint` (Item geometry), `bbox`, or `metadata`/`valid_data` with a metadata `path`. Coverage of an extent does not establish valid or cloud-free pixels. Coverage is also supported for each selected member. Saving is configured independently on the producing plugin’s named result.

## Explicit contracts

Every solver implementation declares a JSON `contract` with `settings_schema`, optional default `settings`, and `goal_schema`. Every goal implementation declares `settings_schema`, optional default `settings`, and the exact solver ID in `solver`. Parameter schemas must explicitly list properties and set `additionalProperties: false`. Configuration cannot replace installed contracts.

The full solver contract is [`backward_chain_contract.json`](../plugins/autostacgis_plugins/backward_chain_contract.json). Its search settings are:

| Parameter | Type | Default | Constraint |
| --- | --- | --- | --- |
| `max_steps` | integer | 64 | At least zero |
| `max_states` | integer | 100000 | At least one |
| `max_bindings` | integer | 100000 | At least one |
| `timeout` | number, seconds | 120 | Greater than zero |

Unknown names and invalid values fail before search. Settings merge in order: implementation defaults, then explicit parameters under `solver.<plugin>`.

The full goal settings schema lives on [`metadata_value.contract`](../plugins/autostacgis_plugins/metadata_value.py). Its expanded output is checked against `backward_chain`'s goal contract before planning. Product presets such as surface reflectance and pansharpening are [configuration examples](../examples/goals).

## One dependency mechanism

Every plugin declares dependencies using unique plugin IDs:

```python
ID = "metadata-value"
CAPABILITY = "goal"
IMPLEMENTATION = metadata_value
REQUIRES = ("backward_chain",)

# Minimal direct-path adapter contract; metadata-value also supports JSONata.
metadata_value.contract = {
    "solver": "backward_chain",
    "settings_schema": {
        "type": "object",
        "properties": {"path": {"type": "string", "minLength": 1}, "value": {}},
        "required": ["path", "value"],
        "additionalProperties": False,
    },
}
```

The solver reference must also occur in `REQUIRES`. Other dependencies, including services, checks, sequences, encoders, and downloaders, use the same tuple. Catalog `requires` lists add dependencies and cannot remove implementation requirements. Nested goal adapters may invoke only their own declared goal dependencies. Names are unique across all capabilities, and entry-point names must match module IDs. Unselected entry points remain lazy.

## Solver execution interface

A solver factory receives `(application, prepared_request, settings)` and returns an instance with:

- `plan(records) -> Plan`: synthesize a workflow without executing processing functions.
- `validate_outputs(plan, records) -> bool`: verify actual and published outputs using that solver's goal semantics.

Goal factories receive `(settings, initial_records, context)` and return JSON parameters in their required solver's dialect. The core expands adapters, detects dependency cycles, checks solver compatibility, and validates the expanded parameters against `goal_schema`.

A Plan carries named steps, initial and predicted records, outputs, cost, and its report. Execution information is held in `module_contracts` and `parameter_templates`; these contain implementation objects and are excluded from the serialized planning report. Initial records must retain their original identity in `runtime.origin` so the core can acquire selected inputs and replan. The executor invokes the selected solver's output validation after execution and any explicitly enabled result saving; it does not assume metadata goal syntax.

The `available` command reports feasibility of the request's declared goal under `requested`; there is no catalog of product-preset plugins to enumerate.
