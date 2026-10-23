from autostacgis.ancillary import descriptor


class DemSource:
    """OpenTopography global DEM, including ellipsoidal SRTM for RPC warps."""

    def discover(self, settings, query, app):
        yield descriptor(settings, query, "digital_elevation_model", "raster")


ID = "dem"
REQUIRES = ("dem-download",)


DemSource.data_in = "dem-download"

CAPABILITY = "metadata_in"
IMPLEMENTATION = DemSource
