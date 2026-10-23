"""The packaged inventory maps former roles to single-capability or reusable plugins."""

import json
import tomllib
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from autostacgis import Application, Registry
from autostacgis.config import validate
from autostacgis.errors import AutoSTACGISError
from autostacgis_plugins import modules

ROOT = Path(__file__).resolve().parents[1]


def test_all_previous_capabilities_have_a_registered_replacement():
    inventory = json.loads((ROOT / "docs/plugin-inventory.json").read_text())
    expected = Counter(
        (row["id"], capability)
        for row in inventory["before"]
        for capability in row["capabilities"]
        if capability != "goal"
    )
    actual = Counter(
        (row["previous"], row["capability"]) for row in inventory["after"] if row["previous"] is not None
    )
    providers = {provider.ID: provider for provider in modules()}
    former_registrations = {row["id"]: row for row in inventory["after_split"]}
    for removed, replacement in inventory["removed_sequence_wrappers"].items():
        previous = former_registrations[removed]["previous"]
        assert removed not in providers
        assert providers[replacement].CAPABILITY == "sequence"
        assert replacement in providers[previous].REQUIRES
        actual[previous, "sequence"] += 1
    assert actual == expected
    assert len(providers) == 82
    assert not set(inventory["removed_goal_presets"]) & set(providers)
    assert set(providers) == {row["id"] for row in inventory["after"]}
    for row in inventory["after"]:
        provider = providers[row["id"]]
        assert provider.CAPABILITY == row["capability"]
        assert provider.VERSION == "1.0.0"
        assert callable(provider.IMPLEMENTATION)
        assert not hasattr(provider, "IMPLEMENTATIONS")


def test_distribution_registers_every_plugin_and_core_registers_none():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    entries = project["project"]["entry-points"]["autostacgis.plugins"]
    assert entries == {provider.ID: provider.__name__ for provider in modules()}
    core = ROOT.parent / "autostacgis-python"
    if core.exists():
        assert not (core / "autostacgis/plugins").exists()
        core_project = tomllib.loads((core / "pyproject.toml").read_text())
        assert "autostacgis.plugins" not in core_project["project"].get("entry-points", {})


@pytest.mark.parametrize("capability", [None, "", "unknown", ["process", "goal"], {"process": lambda: None}])
def test_registration_rejects_missing_unknown_and_plural_capabilities(capability):
    with pytest.raises(AutoSTACGISError, match="exactly one valid capability"):
        Registry(builtins=False).register("invalid", capability, lambda: None)


@pytest.mark.parametrize(
    "capabilities", [{}, {"goal": {"implementation": "one"}, "process": {"implementation": "one"}}]
)
def test_expanded_catalog_rejects_zero_or_multiple_capabilities(capabilities):
    plugin = {"id": "invalid", "capabilities": capabilities}
    with pytest.raises(AutoSTACGISError):
        validate(plugin, "plugin")
    with pytest.raises(AutoSTACGISError):
        Application({"version": "1.0.0", "plugins": [plugin]})


def test_legacy_module_declarations_are_rejected():
    module = SimpleNamespace(ID="legacy", REQUIRES=(), IMPLEMENTATIONS={"goal": lambda: None})
    with pytest.raises(AutoSTACGISError, match="plural IMPLEMENTATIONS"):
        Registry(builtins=False).register_module(module)


@pytest.mark.parametrize(
    "name, capability",
    [
        ("metadata-value", "goal"),
        ("backward_chain", "solver"),
        ("gather-all", "sequence"),
        ("geotiff-metadata", "metadata_out"),
    ],
)
def test_split_roles_load_independently(name, capability):
    app = Application({"version": "1.0.0", "plugins": [{"use": name}]})
    assert set(app.plugins[name]["capabilities"]) == {capability}
    assert "mosaic" not in app.plugins
    assert "geotiff" not in app.plugins


@pytest.mark.parametrize("name", ["eodag", "dem", "atmosphere", "stac-source"])
def test_discovery_loads_a_separate_declared_acquisition_plugin(name):
    app = Application({"version": "1.0.0", "plugins": [{"use": name}]})
    assert set(app.plugins[name]["capabilities"]) == {"metadata_in"}
    assert set(app.plugins[name + "-download"]["capabilities"]) == {"data_in"}
    assert app.sources[name].data_in == name + "-download"
    assert app.scope(name).acquirer(name + "-download") is app.acquirers[name + "-download"]
    with pytest.raises(AutoSTACGISError, match="undeclared dependency"):
        app.scope("buffered-transfer").acquirer(name + "-download")


def test_eodag_discovery_hands_each_product_its_original_download_session(tmp_path, monkeypatch):
    import sys

    calls = []
    gateways = []

    class Page(list):
        def next_page(self, update=False):
            return []

    class Gateway:
        def __init__(self, settings):
            self.number = len(gateways)
            gateways.append(self)

        def search(self, **search):
            return Page([SimpleNamespace(identifier=f"scene-{self.number}")])

        def download(self, product, output_dir, **options):
            calls.append((self.number, product.identifier, options))
            path = Path(output_dir) / (product.identifier + ".tif")
            path.write_bytes(b"downloaded product")
            return str(path)

    def describe(product, rules):
        return {
            "type": "Feature",
            "stac_version": "1.1.0",
            "id": product.identifier,
            "geometry": None,
            "properties": {"datetime": "2026-01-01T00:00:00Z"},
            "links": [],
            "assets": {"data": {"href": f"https://example.test/{product.identifier}.tif", "roles": ["data"]}},
        }

    monkeypatch.setitem(sys.modules, "eodag", SimpleNamespace(EODataAccessGateway=Gateway))
    monkeypatch.setitem(sys.modules, "eodag.config", SimpleNamespace(EODAGSettings=lambda **kwargs: kwargs))
    monkeypatch.setitem(sys.modules, "eodag.autostacgis", SimpleNamespace(describe_product=describe))
    app = Application(
        {
            "version": "1.0.0",
            "plugins": [
                {"use": "eodag"},
                {"use": "eodag-download", "settings": {"download_options": {"extract": False}}},
            ],
        },
        base_dir=tmp_path,
    )
    request = {"sources": ["eodag"], "goal": {"output": {}}}
    first = app.discover(request)[0]
    second = app.discover(request)[0]
    assert calls == []
    assert first.runtime["data_in"] == second.runtime["data_in"] == "eodag-download"
    acquirer = app.scope("eodag").acquirer("eodag-download")
    definition, settings = app.resolve_call("data_in", {"plugin": "eodag-download"})
    for record in (first, second):
        acquirer.acquire(record, settings, app.scope(definition["id"], settings))
        assert Path(record.runtime["local_assets"]["data"]).is_file()
        assert record.item["assets"]["data"]["href"].startswith("https://")
    assert calls == [(0, "scene-0", {"extract": False}), (1, "scene-1", {"extract": False})]
