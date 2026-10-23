from autostacgis.runtime.executors import Pool


class Sequential(Pool):
    backend = "sequential"


ID = "sequential"
REQUIRES = ()

CAPABILITY = "services"
IMPLEMENTATION = Sequential
