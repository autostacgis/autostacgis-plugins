"""Discover STAC items from local documents or an API search."""

from urllib.parse import urljoin, urlsplit

import httpx
from autostacgis.data.kinds import describe_kinds
from autostacgis.errors import AutoSTACGISError
from autostacgis.io import load_item
from autostacgis.model import Record, digest


class StacSource:
    def discover(self, settings, query, app):
        for uri in settings.get("items", []):
            path = uri if urlsplit(uri).scheme else app.path(uri)
            item = load_item(path)
            app.stac.validate(item)
            yield describe_kinds(Record(item, settings.get("type", "raster")), settings.get("type"))
        if settings.get("api_url"):
            url = settings["api_url"].rstrip("/") + "/search"
            body = dict(settings.get("search", {}))
            if "area" in query:
                body["bbox"] = query["area"]
            if "time_range" in query:
                body["datetime"] = "/".join(query["time_range"])
            method = "POST"
            seen = set()
            while url:
                token = digest([url, method, body])
                if token in seen:
                    raise AutoSTACGISError("Recursive STAC search pagination")
                seen.add(token)
                response = httpx.request(method, url, json=body if method == "POST" else None, timeout=60)
                response.raise_for_status()
                page = response.json()
                for item in page["features"]:
                    app.stac.validate(item)
                    yield describe_kinds(Record(item, settings.get("type", "raster")), settings.get("type"))
                link = next((link for link in page.get("links", []) if link["rel"] == "next"), None)
                url = urljoin(url, link["href"]) if link else None
                method = link.get("method", "GET") if link else "GET"
                body = link.get("body") if link else None


ID = "stac-source"
REQUIRES = ("stac-source-download",)


StacSource.data_in = "stac-source-download"

CAPABILITY = "metadata_in"
IMPLEMENTATION = StacSource

VERSION = "1.1.0"
DEPENDENCIES = []
