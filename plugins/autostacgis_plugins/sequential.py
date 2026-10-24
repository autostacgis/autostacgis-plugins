"""Execute submitted work sequentially in the application process."""

from autostacgis.runtime.executors import Pool


class Sequential(Pool):
    backend = "sequential"


ID = "sequential"
REQUIRES = ()

CAPABILITY = "services"
IMPLEMENTATION = Sequential

VERSION = "1.1.0"
DEPENDENCIES = []
