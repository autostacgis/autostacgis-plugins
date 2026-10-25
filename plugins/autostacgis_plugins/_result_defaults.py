"""Reusable defaults declared by the standard processing plugins."""

from copy import deepcopy


def result_defaults(function, *, suffix):
    """Describe optional saving without enabling it or loading an encoder."""
    contract = function.contract
    anchor = contract.get("anchor", next(iter(contract["argument_requirements"])))
    for port, output in contract["outputs"].items():
        individual = bool(output.get("each_from")) or (
            contract["argument_requirements"][anchor].get("cardinality", "one") == "one"
            and output.get("geometry") != "union"
        )
        encoder, extension = {
            "raster": ("geotiff", ".tif"),
            "vector": ("parquet", ".parquet"),
            "table": ("parquet", ".parquet"),
        }.get(output["kind"], (None, ".bin"))
        # All path choices live here in plugin defaults, not in the executor.
        directory = "item.properties.`data_state:output_directory`"
        name = 'source_id & (source_asset = "data" ? "" : "_" & source_asset)' if individual else "item.id"
        expression = (
            f"($directory := {directory}; "
            '$assert($type($directory) = "string" and $length($directory) > 0, '
            '"Set data_state:output_directory or override this result destination path"); '
            f'$name := $replace({name}, /[^A-Za-z0-9._-]/, "_"); '
            '$tokens := $join(asset.`data_state:filename_suffixes`, "_"); '
            '$directory & "/" & $name & ($length($tokens) > 0 ? "_" & $tokens : "") '
            f'& "{extension}")'
        )
        defaults = {
            "save": False,
            "filename_suffixes": [suffix, *([port] if len(contract["outputs"]) > 1 else [])],
            "data_out": {"plugin": "filesystem", "settings": {"path": {"jsonata": expression}}},
            "output_directory": {
                "jsonata": '(item.properties.`data_state:output_directory` ? item.properties.`data_state:output_directory` : "output/" & $replace(source_id, /[^A-Za-z0-9._-]/, "_"))'
            }
            if individual
            else "output",
        }
        if encoder and set(output["data_types"]) & {"raster", "batches"}:
            defaults["encode"] = {"plugin": encoder}
        for key, value in defaults.items():
            output.setdefault(key, deepcopy(value))
