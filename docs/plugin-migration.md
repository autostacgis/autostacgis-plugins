# Plugin migration inventory

Before: **81 plugins** in `autostacgis-python/autostacgis/plugins`.
After: **82 plugins**, each with one capability, in `autostacgis-plugins/plugins/autostacgis_plugins`.

The initial split produced 97 registrations. Removing 11 goal presets and seven redundant sequence wrappers, then adding `backward_chain` and `metadata-value`, gives 81 installed registrations before replacing `scheduler` with `apscheduler` and adding `watchdog`, for 82 current registrations. Product goals are configuration, and collection processors depend directly on reusable `gather-all`. The default catalog selects 81 implementations; select `metadata-value` explicitly when using that generic goal adapter. The machine-readable `after_split` list is historical; `after` lists the current catalog.

## Before

| Plugin | Declared capabilities |
| --- | --- |
| `align_grid` | `process` |
| `apply_mask` | `process` |
| `atmosphere` | `metadata_in`, `data_in` |
| `atmosphere-for-image` | `checks` |
| `atmospheric_correction` | `process` |
| `autostacgis.execution/v1` | `extensions` |
| `band_math` | `process` |
| `buffered-transfer` | `data_transfer` |
| `clean_footprints` | `process` |
| `cli` | `trigger` |
| `cog` | `encode`, `metadata_out` |
| `combine` | `sequence` |
| `common-crs` | `checks` |
| `compatible-grids` | `checks` |
| `compatible-optical` | `checks` |
| `dask` | `services` |
| `dem` | `metadata_in`, `data_in` |
| `detect_clouds` | `process` |
| `eodag` | `metadata_in`, `data_in` |
| `eoreader` | `metadata_in` |
| `events` | `services` |
| `executor` | `services` |
| `explicit-groups` | `sequence` |
| `extract_footprints` | `process`, `sequence` |
| `file-checkpoint` | `checkpoint` |
| `filesystem` | `data_out` |
| `filter` | `sequence`, `goal` |
| `for-each` | `goal` |
| `gather-all` | `sequence` |
| `geotiff` | `encode`, `metadata_out` |
| `global_radiometric_match` | `process`, `sequence` |
| `group-by` | `sequence` |
| `harmonized-mosaic` | `goal` |
| `has-role` | `checks` |
| `joint_coregistration` | `process`, `sequence` |
| `local_radiometric_match` | `process`, `sequence` |
| `markov_seamlines` | `process`, `sequence` |
| `mask_by_polygons` | `process` |
| `masked` | `goal` |
| `merge_vectors` | `process` |
| `metadata-matches` | `checks` |
| `metadata-schema` | `checks` |
| `mosaic` | `process`, `sequence`, `goal` |
| `multiprocessing` | `services` |
| `normalized` | `goal` |
| `normalized-pansharpened` | `goal` |
| `opentelemetry` | `services` |
| `orthorectify_rpc` | `process` |
| `output` | `goal` |
| `overlap` | `sequence` |
| `pansharpen` | `process` |
| `pansharpened` | `goal` |
| `parquet` | `encode` |
| `polygonize` | `process` |
| `python` | `trigger` |
| `rasterize_point_attribute` | `process` |
| `register_to_reference` | `process` |
| `registered` | `goal` |
| `s3` | `data_out` |
| `same-fields` | `checks` |
| `sample_dem` | `process` |
| `scheduler` | `trigger` |
| `sequential` | `services` |
| `slurm` | `trigger` |
| `source-member` | `checks` |
| `split` | `sequence` |
| `stac-api` | `metadata_out` |
| `stac-item` | `metadata_out` |
| `stac-json` | `metadata_out` |
| `stac-resolver` | `metadata_in` |
| `stac-source` | `metadata_in`, `data_in` |
| `staging` | `services` |
| `statistics` | `process` |
| `storage` | `services` |
| `surface-reflectance` | `goal` |
| `table` | `metadata_in` |
| `threads` | `services` |
| `valid-data` | `checks` |
| `voronoi_seamlines` | `process` |
| `weighted_seamlines` | `process`, `sequence` |
| `zarr` | `encode`, `metadata_out` |

## After

| Plugin | Capability | Module |
| --- | --- | --- |
| `align_grid` | `process` | `autostacgis_plugins.align_grid` |
| `apply_mask` | `process` | `autostacgis_plugins.apply_mask` |
| `apscheduler` | `trigger` | `autostacgis_plugins.apscheduler` |
| `atmosphere` | `metadata_in` | `autostacgis_plugins.atmosphere` |
| `atmosphere-download` | `data_in` | `autostacgis_plugins.atmosphere_download` |
| `atmosphere-for-image` | `checks` | `autostacgis_plugins.atmosphere_for_image` |
| `atmospheric_correction` | `process` | `autostacgis_plugins.atmospheric_correction` |
| `autostacgis.execution/v1` | `extensions` | `autostacgis_plugins.execution` |
| `backward_chain` | `solver` | `autostacgis_plugins.backward_chain` |
| `band_math` | `process` | `autostacgis_plugins.band_math` |
| `buffered-transfer` | `data_transfer` | `autostacgis_plugins.buffered_transfer` |
| `clean_footprints` | `process` | `autostacgis_plugins.clean_footprints` |
| `cli` | `trigger` | `autostacgis_plugins.cli` |
| `cog` | `encode` | `autostacgis_plugins.cog` |
| `cog-metadata` | `metadata_out` | `autostacgis_plugins.cog_metadata` |
| `combine` | `sequence` | `autostacgis_plugins.combine` |
| `common-crs` | `checks` | `autostacgis_plugins.common_crs` |
| `compatible-grids` | `checks` | `autostacgis_plugins.compatible_grids` |
| `compatible-optical` | `checks` | `autostacgis_plugins.compatible_optical` |
| `dask` | `services` | `autostacgis_plugins.dask` |
| `dem` | `metadata_in` | `autostacgis_plugins.dem` |
| `dem-download` | `data_in` | `autostacgis_plugins.dem_download` |
| `detect_clouds` | `process` | `autostacgis_plugins.detect_clouds` |
| `eodag` | `metadata_in` | `autostacgis_plugins.eodag` |
| `eodag-download` | `data_in` | `autostacgis_plugins.eodag_download` |
| `eoreader` | `metadata_in` | `autostacgis_plugins.eoreader` |
| `events` | `services` | `autostacgis_plugins.events` |
| `executor` | `services` | `autostacgis_plugins.executor` |
| `explicit-groups` | `sequence` | `autostacgis_plugins.explicit_groups` |
| `extract_footprints` | `process` | `autostacgis_plugins.extract_footprints` |
| `file-checkpoint` | `checkpoint` | `autostacgis_plugins.file_checkpoint` |
| `filesystem` | `data_out` | `autostacgis_plugins.filesystem` |
| `filter` | `sequence` | `autostacgis_plugins.filter` |
| `gather-all` | `sequence` | `autostacgis_plugins.gather_all` |
| `geotiff` | `encode` | `autostacgis_plugins.geotiff` |
| `geotiff-metadata` | `metadata_out` | `autostacgis_plugins.geotiff_metadata` |
| `global_radiometric_match` | `process` | `autostacgis_plugins.global_radiometric_match` |
| `group-by` | `sequence` | `autostacgis_plugins.group_by` |
| `has-role` | `checks` | `autostacgis_plugins.has_role` |
| `joint_coregistration` | `process` | `autostacgis_plugins.joint_coregistration` |
| `local_radiometric_match` | `process` | `autostacgis_plugins.local_radiometric_match` |
| `markov_seamlines` | `process` | `autostacgis_plugins.markov_seamlines` |
| `mask_by_polygons` | `process` | `autostacgis_plugins.mask_by_polygons` |
| `merge_vectors` | `process` | `autostacgis_plugins.merge_vectors` |
| `metadata-matches` | `checks` | `autostacgis_plugins.metadata_matches` |
| `metadata-schema` | `checks` | `autostacgis_plugins.metadata_schema` |
| `metadata-value` | `goal` | `autostacgis_plugins.metadata_value` |
| `mosaic` | `process` | `autostacgis_plugins.mosaic` |
| `multiprocessing` | `services` | `autostacgis_plugins.multiprocessing` |
| `opentelemetry` | `services` | `autostacgis_plugins.opentelemetry` |
| `orthorectify_rpc` | `process` | `autostacgis_plugins.orthorectify_rpc` |
| `overlap` | `sequence` | `autostacgis_plugins.overlap` |
| `pansharpen` | `process` | `autostacgis_plugins.pansharpen` |
| `parquet` | `encode` | `autostacgis_plugins.parquet` |
| `polygonize` | `process` | `autostacgis_plugins.polygonize` |
| `now` | `trigger` | `autostacgis_plugins.now` |
| `rasterize_point_attribute` | `process` | `autostacgis_plugins.rasterize_point_attribute` |
| `register_to_reference` | `process` | `autostacgis_plugins.register_to_reference` |
| `s3` | `data_out` | `autostacgis_plugins.s3` |
| `same-fields` | `checks` | `autostacgis_plugins.same_fields` |
| `sample_dem` | `process` | `autostacgis_plugins.sample_dem` |
| `sequential` | `services` | `autostacgis_plugins.sequential` |
| `slurm` | `trigger` | `autostacgis_plugins.slurm` |
| `source-member` | `checks` | `autostacgis_plugins.source_member` |
| `split` | `sequence` | `autostacgis_plugins.split` |
| `stac-api` | `metadata_out` | `autostacgis_plugins.stac_api` |
| `stac-item` | `metadata_out` | `autostacgis_plugins.stac_item` |
| `stac-json` | `metadata_out` | `autostacgis_plugins.stac_json` |
| `stac-resolver` | `metadata_in` | `autostacgis_plugins.stac_resolver` |
| `stac-source` | `metadata_in` | `autostacgis_plugins.stac_source` |
| `stac-source-download` | `data_in` | `autostacgis_plugins.stac_source_download` |
| `staging` | `services` | `autostacgis_plugins.staging` |
| `statistics` | `process` | `autostacgis_plugins.statistics` |
| `storage` | `services` | `autostacgis_plugins.storage` |
| `table` | `metadata_in` | `autostacgis_plugins.table` |
| `threads` | `services` | `autostacgis_plugins.threads` |
| `valid-data` | `checks` | `autostacgis_plugins.valid_data` |
| `voronoi_seamlines` | `process` | `autostacgis_plugins.voronoi_seamlines` |
| `watchdog` | `trigger` | `autostacgis_plugins.watchdog` |
| `weighted_seamlines` | `process` | `autostacgis_plugins.weighted_seamlines` |
| `zarr` | `encode` | `autostacgis_plugins.zarr` |
| `zarr-metadata` | `metadata_out` | `autostacgis_plugins.zarr_metadata` |

## Sequence wrappers replaced by gather-all

These removed registrations only forwarded unchanged inputs to `gather-all`. Their processing plugins already declare `gather-all` in `REQUIRES` and in their collection-input contracts. Change explicit catalog selections and request sequence overrides to `gather-all`.

| Removed registration | Replacement |
| --- | --- |
| `extract_footprints-sequence` | `gather-all` |
| `global_radiometric_match-sequence` | `gather-all` |
| `joint_coregistration-sequence` | `gather-all` |
| `local_radiometric_match-sequence` | `gather-all` |
| `markov_seamlines-sequence` | `gather-all` |
| `mosaic-sequence` | `gather-all` |
| `weighted_seamlines-sequence` | `gather-all` |

Distinct grouping plugins remain: `combine`, `explicit-groups`, `filter`, `gather-all`, `group-by`, `overlap`, and `split`.

## Goal presets moved to configuration

| Removed registration | Replacement |
| --- | --- |
| `filter-goal` | `goal.for_each` |
| `for-each` | `goal.for_each` |
| `harmonized-mosaic` | [`harmonized-mosaic.yaml`](../examples/goals/harmonized-mosaic.yaml) |
| `masked` | [`masked.yaml`](../examples/goals/masked.yaml) |
| `mosaic-goal` | [`mosaic-goal.yaml`](../examples/goals/mosaic-goal.yaml) |
| `normalized` | [`normalized.yaml`](../examples/goals/normalized.yaml) |
| `normalized-pansharpened` | [`normalized-pansharpened.yaml`](../examples/goals/normalized-pansharpened.yaml) |
| `output` | `goal.output` |
| `pansharpened` | [`pansharpened.yaml`](../examples/goals/pansharpened.yaml) |
| `registered` | [`registered.yaml`](../examples/goals/registered.yaml) |
| `surface-reflectance` | [`surface-reflectance.yaml`](../examples/goals/surface-reflectance.yaml) |

## Capability splits

| Original plugin | Current registrations |
| --- | --- |
| `atmosphere` | `atmosphere` (metadata_in), `atmosphere-download` (data_in) |
| `cog` | `cog` (encode), `cog-metadata` (metadata_out) |
| `dem` | `dem` (metadata_in), `dem-download` (data_in) |
| `eodag` | `eodag` (metadata_in), `eodag-download` (data_in) |
| `extract_footprints` | `extract_footprints` (process), uses `gather-all` (sequence) |
| `filter` | `filter` (sequence) |
| `geotiff` | `geotiff` (encode), `geotiff-metadata` (metadata_out) |
| `global_radiometric_match` | `global_radiometric_match` (process), uses `gather-all` (sequence) |
| `joint_coregistration` | `joint_coregistration` (process), uses `gather-all` (sequence) |
| `local_radiometric_match` | `local_radiometric_match` (process), uses `gather-all` (sequence) |
| `markov_seamlines` | `markov_seamlines` (process), uses `gather-all` (sequence) |
| `mosaic` | `mosaic` (process), uses `gather-all` (sequence) |
| `stac-source` | `stac-source` (metadata_in), `stac-source-download` (data_in) |
| `weighted_seamlines` | `weighted_seamlines` (process), uses `gather-all` (sequence) |
| `zarr` | `zarr` (encode), `zarr-metadata` (metadata_out) |

All dependencies use `REQUIRES = ("unique-plugin-id", ...)`. The same names are used in catalog `requires` arrays and `{plugin: name}` references. Missing names, cycles, duplicate IDs, and entry-point aliases that disagree with the module ID are errors. Each goal plugin names its solver in `IMPLEMENTATION.contract["solver"]` and includes that exact name in `REQUIRES`.

Encoders load their `*-metadata` writers as dependencies; discovery loads its `*-download` acquirer. Configure acquisition settings on the download registration. Discovery explicitly routes records through `data_in`; EODAG shares its search session through scoped `context.acquirer()` access.

The entry-point group remains `autostacgis.plugins`; Python imports use `autostacgis_plugins.<module>`. The custom example is `examples/scale_plugin.py`. See [solver and goal contracts](solvers.md).

## Timed and file triggers

The former `scheduler` registration is replaced by `apscheduler`. Time-based jobs use APScheduler trigger aliases and raw scheduler, trigger, job, and start options. `watchdog` handles file events with native or polling observers. Both implementations live in the Python library; see [trigger configuration](https://github.com/autostacgis/autostacgis-python/blob/main/docs/triggers.md).

The immediate Python trigger is named `now` in the current catalog. It replaces the former `python` registration; omitted triggers also run immediately.
