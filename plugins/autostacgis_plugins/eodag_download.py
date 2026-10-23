from pathlib import Path
from urllib.parse import urlsplit

from autostacgis.errors import AutoSTACGISError
from autostacgis.io import local


class EodagDownload:
    def __init__(self):
        self.products = {}

    def acquire(self, record, settings, app):
        directory = app.path(settings.get("download_directory", str(app.work / "downloads")))
        directory.mkdir(parents=True, exist_ok=True)
        options = dict(settings.get("download_options", {}))
        if "output_dir" in options:
            raise AutoSTACGISError("Use download_directory")
        gateway, product = self.products[record.key]
        path = gateway.download(product, output_dir=str(directory), **options)
        if not path or not local(path).exists():
            raise AutoSTACGISError("EODAG did not acquire a local product")
        location = local(path).resolve()
        record.runtime["product_path"] = str(location)
        # EODAG retains provider URLs; map downloaded files without overwriting them.
        for name, asset in record.item.get("assets", {}).items():
            basename = Path(urlsplit(asset["href"]).path).name
            candidates = list(location.rglob(basename)) if location.is_dir() and basename else []
            if location.is_file() and location.name == basename:
                candidates = [location]
            if len(candidates) > 1:
                raise AutoSTACGISError(f"Ambiguous acquired asset {name}: {basename}")
            if candidates:
                record.runtime.setdefault("local_assets", {})[name] = str(candidates[0])
        return record


ID = "eodag-download"
CAPABILITY = "data_in"
IMPLEMENTATION = EodagDownload
REQUIRES = ()

VERSION = "1.0.0"
DEPENDENCIES = [
    "eodag @ git+https://github.com/autostacgis/eodag.git@016be9ce5196d0f7e607d9f1bb9d56296e2d233f"
]
