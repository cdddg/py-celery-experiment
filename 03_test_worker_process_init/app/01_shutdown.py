import logging
from logging import getLogger

import os
from datetime import timedelta

import colorlog
from celery import Celery
from celery.signals import (
    celeryd_after_setup, celeryd_init, worker_init,
    worker_before_create_process, worker_ready,
    worker_shutting_down, worker_process_init, worker_process_shutdown,
    worker_shutdown, setup_logging,
)


app = Celery(
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    broker_connection_retry_on_startup=True,
    beat_schedule_filename='celerybeat-schedule',
    beat_schedule={
        'test-job': {
            'task': f'{__name__}.test_task',
            'schedule': timedelta(seconds=10),
        },
    },
    worker_concurrency=1,
)
app.conf.update(
    worker_hijack_root_logger=False
)


def setup_colored_logging():
    logger = getLogger(__name__)
    formatter = colorlog.ColoredFormatter(
        fmt='%(asctime)s.%(msecs)03d| %(log_color)s%(levelname)-8s%(reset)s| %(process)-5s | %(processName)-33s | %(log_color)s%(message)s%(reset)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        },
        secondary_log_colors={},
        style='%',
    )
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)


@celeryd_after_setup.connect
def celeryd_after_setup_handler(sender=None, instance=None, **kwargs):
    getLogger(__name__).info("celeryd_after_setup: sender=%s, instance=%s", sender, instance)


@celeryd_init.connect
def celeryd_init_handler(**kwargs):
    getLogger(__name__).info("celeryd_init")


@worker_init.connect
def worker_init_handler(**kwargs):
    getLogger(__name__).info("worker_init")


@worker_before_create_process.connect
def worker_before_create_process_handler(**kwargs):
    getLogger(__name__).info("worker_before_create_process")


@worker_ready.connect
def worker_ready_handler(**kwargs):
    getLogger(__name__).info("worker_ready")


@worker_shutting_down.connect
def worker_shutting_down_handler(**kwargs):
    getLogger(__name__).info("worker_shutting_down")


@worker_process_init.connect
def worker_process_init_handler(**kwargs):
    logger = getLogger(__name__)

    logger.info("worker_process_init")
    logger.warning('worker_process_init: Shutting down the application control...')
    app.control.shutdown()
    logger.warning('worker_process_init: Application control shutdown complete.')


@worker_process_shutdown.connect
def worker_process_shutdown_handler(**kwargs):
    getLogger(__name__).info("worker_process_shutdown")


@worker_shutdown.connect
def worker_shutdown_handler(**kwargs):
    getLogger(__name__).info("worker_shutdown")


@setup_logging.connect
def on_on_show_logging(**kwargs):
    getLogger(__name__).info("setup_logging")


@app.task
def test_task() -> None:
    getLogger(__name__).info('test_task: Running test task...')


setup_colored_logging()
