"""Discover imagery through configured EODAG providers."""

from itertools import chain

from autostacgis.errors import AutoSTACGISError
from autostacgis.model import Record


class EodagSource:
    def __init__(self):
        self.gateway = None

    def discover(self, settings, query, app):
        from eodag import EODataAccessGateway
        from eodag.autostacgis import describe_product
        from eodag.config import EODAGSettings

        downloader = app.acquirer("eodag-download")
        self.gateway = EODataAccessGateway(settings=EODAGSettings(**settings.get("config", {})))
        search = dict(settings.get("search", {}))
        if "area" in query:
            search["geom"] = query["area"]
        if "time_range" in query:
            search.update(start=query["time_range"][0], end=query["time_range"][1])
        if "lookback_hours" in query:
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)
            search.update(
                start=(now - timedelta(hours=query["lookback_hours"])).isoformat(), end=now.isoformat()
            )
        if "page" in search or "raise_errors" in search:
            raise AutoSTACGISError("EODAG pagination is managed by AutoSTACGIS")
        first = self.gateway.search(**search, raise_errors=True)
        first.raise_errors = True
        for page in chain([first], first.next_page(update=False)):
            for product in page:
                item = describe_product(product, settings.get("state_rules", []))
                record = Record(item, settings.get("type", "raster"))
                downloader.products[record.key] = (self.gateway, product)
                record.runtime["original_id"] = item["id"]
                yield record


ID = "eodag"
REQUIRES = ("eodag-download",)


EodagSource.data_in = "eodag-download"

CAPABILITY = "metadata_in"
IMPLEMENTATION = EodagSource

VERSION = "1.1.0"
DEPENDENCIES = [
    "eodag @ git+https://github.com/autostacgis/eodag.git@016be9ce5196d0f7e607d9f1bb9d56296e2d233f"
]
