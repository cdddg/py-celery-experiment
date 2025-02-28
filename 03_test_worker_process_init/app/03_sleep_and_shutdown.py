import os
import signal
import sys
from logging import getLogger

from celery.signals import worker_process_init

from .base import app


@worker_process_init.connect
def worker_process_init_handler(**kwargs):
    logger = getLogger(__package__)

    logger.info('worker_process_init')

    import time
    for _ in range(5):
        logger.debug('Sleeping for 1 second...')
        time.sleep(1)

    logger.warning('worker_process_init: Shutting down the application control...')
    app.control.shutdown()
    logger.warning('worker_process_init: Application control shutdown complete.')
