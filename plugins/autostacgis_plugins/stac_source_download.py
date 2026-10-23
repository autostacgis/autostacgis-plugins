from pathlib import Path
from urllib.parse import urlsplit

import httpx
from autostacgis.model import digest


class StacDownload:
    def acquire(self, record, settings, app):
        if not settings.get("download", False):
            return record
        directory = app.work / "downloads" / record.key
        directory.mkdir(parents=True, exist_ok=True)
        for name, asset in record.item["assets"].items():
            href = asset["href"]
            if href.startswith(("https://", "http://")):
                target = directory / (digest(name)[:12] + Path(urlsplit(href).path).suffix)
                temporary = target.with_suffix(target.suffix + ".part")
                with httpx.stream("GET", href, timeout=120, follow_redirects=True) as response:
                    response.raise_for_status()
                    with temporary.open("wb") as stream:
                        for block in response.iter_bytes():
                            stream.write(block)
                temporary.replace(target)
                record.runtime.setdefault("local_assets", {})[name] = str(target)
        return record


ID = "stac-source-download"
CAPABILITY = "data_in"
IMPLEMENTATION = StacDownload
REQUIRES = ()

VERSION = "1.0.0"
DEPENDENCIES = []
