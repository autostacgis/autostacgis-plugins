"""Acquire atmospheric auxiliary datasets selected during discovery."""

from datetime import datetime

import httpx
import numpy as np
from autostacgis.data import Batches
from autostacgis.errors import AutoSTACGISError


class AtmosphereDownload:
    def acquire(self, record, settings, app):
        import pyarrow as pa

        day = datetime.fromisoformat(record.runtime["time_range"][0].replace("Z", "+00:00")).strftime(
            "%Y%m%d"
        )
        west, south, east, north = record.runtime["area"]
        size = settings.get("grid_size", 1)
        if size < 1:
            raise AutoSTACGISError("Atmosphere grid_size must be positive")
        xs = np.linspace(west, east, size) if size > 1 else [(west + east) / 2]
        ys = np.linspace(south, north, size) if size > 1 else [(south + north) / 2]
        values = {key: [] for key in ("aot550", "water_vapor", "ozone")}
        for x in xs:
            for y in ys:
                response = httpx.get(
                    settings.get("endpoint", "https://power.larc.nasa.gov/api/temporal/daily/point"),
                    params={
                        "parameters": "AOD_55,PW,TO3",
                        "community": "RE",
                        "longitude": float(x),
                        "latitude": float(y),
                        "start": day,
                        "end": day,
                        "format": "JSON",
                    },
                    timeout=60,
                )
                response.raise_for_status()
                payload = response.json()
                for provider, name, factor in [
                    ("AOD_55", "aot550", 1),
                    ("PW", "water_vapor", 1),
                    ("TO3", "ozone", 0.001),
                ]:
                    value = payload.get("properties", {}).get("parameter", {}).get(provider, {}).get(day)
                    if (
                        value is not None
                        and value != payload.get("header", {}).get("fill_value", -999)
                        and value >= 0
                    ):
                        values[name].append(float(value) * factor)
        parameters = {key: float(np.mean(value)) if value else None for key, value in values.items()}
        parameters.update(settings.get("parameters", {}))
        parameters.update(month=int(day[4:6]), day=int(day[6:8]))
        record.item["properties"]["autostacgis:atmosphere"] = parameters
        record.item["properties"]["autostacgis:atmosphere_source"] = "NASA POWER"
        record.payload = Batches(pa.Table.from_pylist([parameters]).to_batches(), kind="table")
        return record


ID = "atmosphere-download"
CAPABILITY = "data_in"
IMPLEMENTATION = AtmosphereDownload
REQUIRES = ()

VERSION = "0.0.1"
DEPENDENCIES = []
