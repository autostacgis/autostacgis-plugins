"""Encode raster results in chunked Zarr storage."""

from autostacgis.encoding import encode, restore


def zarr_writer(record, settings, context):
    return encode(record, settings, context, "zarr")


def open_artifact(saved, record, settings):
    return restore(saved, record, settings, "zarr")


zarr_writer.restore = open_artifact


zarr_writer.extension = ".zarr"
zarr_writer.suffixes = [".zarr"]
zarr_writer.input_types = ["raster"]
zarr_writer.output_types = ["path"]
ID = "zarr"
REQUIRES = ("zarr-metadata",)

CAPABILITY = "encode"
IMPLEMENTATION = zarr_writer

VERSION = "1.1.0"
DEPENDENCIES = []
