# AutoSTACGIS plugins

The standard AutoSTACGIS plugins live in [`plugins/autostacgis_plugins`](plugins/autostacgis_plugins). Each plugin module declares exactly one capability and one implementation. Shared libraries can support several independently registered plugins.

Install alongside the sibling implementation checkout:

```sh
python -m pip install -e ../autostacgis-python -e '.[dev]'
```

Optional integrations are extras of this distribution, for example `.[atmosphere,spectralmatch,registration,cloud,pointcloud,distributed,triggers,s3,telemetry]`. The pinned EODAG and EOReader library forks remain under `autostacgis-python/external`; install those libraries when using their adapters.

A plugin declaration is explicit:

```python
ID = "my-processing"
CAPABILITY = "process"
IMPLEMENTATION = process
REQUIRES = ("storage",)
DEFAULTS = {}  # Settings for this plugin's sole capability.
```

```toml
[project.entry-points."autostacgis.plugins"]
my-processing = "my_package.my_processing"
```

Programmatic registration uses `registry.register("my-processing", "process", process, requires=("storage",))`. Capability maps and plural `IMPLEMENTATIONS` module declarations are rejected. Expanded catalog declarations retain the `capabilities` object, which must contain exactly one explicitly named capability.

Catalogs select registrations with `plugins: [{use: my-processing}]`. Declared dependencies load recursively. Unselected third-party registrations are not imported. The core's default catalog delegates to this installed package.

Collection-processing plugins depend directly on reusable sequence plugins such as `gather-all` and select them in their input contracts. Add a sequence plugin when it implements distinct grouping behavior. See the [removed wrapper replacements](docs/plugin-migration.md#sequence-wrappers-replaced-by-gather-all).

- [Complete before-and-after plugin lists and migration mapping](docs/plugin-migration.md)
- [Solver and goal contracts](docs/solvers.md)
- [Machine-readable inventory](docs/plugin-inventory.json)
- [Custom processing plugin example](examples/scale_plugin.py)
- [Core plugin authoring guide](https://github.com/autostacgis/autostacgis-python/blob/main/docs/plugins.md)

Run `pytest tests ../autostacgis-python/tests`, `ruff check plugins examples tests`, and `ruff format --check plugins examples tests`. Build with `python -m build`.

Product goals are declarative configuration. The generic `metadata-value` goal adapter requires `backward_chain` and solves for direct-path or JSONata values. JSONata spatial predicates select or require coverage from bbox, polygon, or custom geometry metadata. Only one solver can be active. Solver settings and accepted goals are explicit JSON Schema contracts. See [solver documentation and AOI examples](docs/solvers.md).

Plugin publication and file installation: [CONTRIBUTING.md](CONTRIBUTING.md). The versioned online catalog is published by `.github/workflows/registry.yml`.

Each published module declares a semantic `VERSION` and optional `DEPENDENCIES` (PEP 508 Python library requirements). `REQUIRES` continues to name other plugins. The package version and each plugin version are independent.
