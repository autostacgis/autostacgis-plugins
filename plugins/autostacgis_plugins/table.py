"""Read tabular assets into the common exchange representation."""

from autostacgis.ancillary import descriptor
from autostacgis.data import Batches


class TableSource:
    """Explicit JSON parameters as a typed Arrow table, e.g. calibrated atmosphere."""

    def discover(self, settings, query, app):
        import pyarrow as pa

        record = descriptor(settings, query, settings.get("content", "atmosphere"), "table")
        values = settings["values"]
        record.payload = Batches(
            pa.Table.from_pylist(values if isinstance(values, list) else [values]).to_batches()
        )
        yield record

    def acquire(self, record, settings, app):
        return record


ID = "table"
REQUIRES = ()

CAPABILITY = "metadata_in"
IMPLEMENTATION = TableSource

VERSION = "1.1.0"
DEPENDENCIES = []
