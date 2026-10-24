"""Execute plugin work in the shared Python multiprocessing pool."""

from autostacgis.runtime.executors import Pool


class Processes(Pool):
    def create_pool(self):
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor

        from autostacgis.runtime.executors import _process_init

        return ProcessPoolExecutor(
            max_workers=self.workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_process_init,
        )

    resource_group = "executor"


ID = "multiprocessing"
REQUIRES = ()

CAPABILITY = "services"
IMPLEMENTATION = Processes

VERSION = "1.1.0"
DEPENDENCIES = []
