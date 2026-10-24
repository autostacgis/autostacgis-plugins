# Publishing an AutostacGIS plugin

Plugins are single Python modules in `plugins/autostacgis_plugins/`. Their public namespace is `autostacgis_plugins`; names (`ID`) are globally unique. Each module provides exactly one capability. Reuse existing bundled helpers or a versioned Python library, rather than publishing forwarding wrappers. New shared helpers must be shipped in a declared Python dependency so a single-file installation can retrieve them.

1. Fork this repository and add `plugins/autostacgis_plugins/my_plugin.py`.
2. Declare literal `ID`, `VERSION` (semantic version), `CAPABILITY`, and `REQUIRES` (plugin IDs). Set `IMPLEMENTATION` to the capability implementation. Optional `DEPENDENCIES` contains PEP 508 Python package requirements; a descriptive module docstring is required. See an existing module of the same capability for the callable interface. Goals must name their required solver in both `REQUIRES` and the explicit goal contract.
3. Include a meaningful example/test. Settings and solver parameters must have explicit JSON Schema contracts. Do not include credentials or import-time side effects. Required shared Python libraries must be installable using `DEPENDENCIES` when installing the file alone.
4. Run `python scripts/build_manifest.py`. Add the generated `plugins.json`. Add the module's entry point to `pyproject.toml` for inclusion in the complete distribution. Run the repository tests.
5. Open a PR describing its capability, dependencies, inputs, outputs, and version. Maintainers review and merge it. Enable GitHub Pages with **GitHub Actions** as the source once for this repository.

On merge, Actions publishes `https://autostacgis.github.io/autostacgis-plugins/plugins.json`. Each source URL is pinned to the merged commit and includes its SHA-256 checksum. Clients discover the catalog online and request installation on their connected backend. Bump `VERSION` whenever a module changes (patch for fixes, minor for compatible additions, major for breaking contracts). Old installed versions remain in the local version store; installing a newer version changes the active index. The bundled Python distribution has its own version independent of individual plugins.

Example declarations:

```python
ID = "my-check"
VERSION = "1.0.0"
CAPABILITY = "checks"
REQUIRES = []
DEPENDENCIES = []
# IMPLEMENTATION = MyCheck  # implement the checks interface used by the engine
```

A user may also install a local `.py` file through either GUI without publishing it. It uses the same declarations and validation. Installation copies the version into the backend's private plugin store under `autostacgis_plugins`, installs its declared Python dependencies, and verifies the single-capability contract before activating it. It does not write into the application's bundled files. A new workflow uses the active versions; avoid changing plugins while jobs are running.

Plugins are executable Python with the permissions of the connected backend. Install reviewed code from maintainers you trust. The checksum verifies the published bytes; it does not audit their behavior. Remote clients need the backend write token to install anything. The manifest URL can be configured on the backend with `AUTOSTACGIS_PLUGIN_REGISTRY_URL` for an organization's registry.

Native dependencies remain environment prerequisites where no compatible Python wheel exists. Plugins using `osgeo` declare GDAL; provide a matching GDAL runtime/development installation for its Python bindings (the core repository environment.yml supplies the Conda setup). Atmospheric correction also needs the native 6S executable. The EOReader and EODAG adapters use the pinned AutostacGIS forks because they provide the required STAC integration APIs. Publish those referenced commits before publishing dependent plugin versions.

## Required description and workflow defaults

Begin the Python file with a descriptive module docstring; it is required by the registry validator and installer and displayed by both GUIs and `autostacgis plugins list`. A separate `DESCRIPTION` variable is unnecessary. Document parameter types, descriptions, and defaults in `IMPLEMENTATION.settings_schema` or the contract's `settings_schema`. Simple function annotations can supplement a missing explicit schema; complex types are not guessed.

`DEFAULTS` is the parameter object for this plugin. Optional literal `DEFAULT_CONFIG` provides capability-grouped defaults for supporting plugins, for example `{"sequence": {"gather-all": {}}}`. Referenced names are added to `REQUIRES` automatically. User settings override the fragment. Selecting a helper does not call it: name the check/sequence in the actual processing contract as well. Every plugin remains one capability; solver and trigger selections are exclusive.
