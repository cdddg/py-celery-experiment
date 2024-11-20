import logging
import os
from datetime import timedelta

from celery import Celery
from celery.signals import (
    # Task signals
    before_task_publish, after_task_publish, task_prerun, task_postrun,
    task_retry, task_success, task_failure, task_internal_error,
    task_received, task_revoked, task_unknown, task_rejected,

    # App signals
    import_modules,

    # Worker signals
    celeryd_after_setup, celeryd_init, worker_init,
    worker_before_create_process, worker_ready, heartbeat_sent,
    worker_shutting_down, worker_process_init, worker_process_shutdown,
    worker_shutdown,

    # Beat signals
    beat_init, beat_embedded_init,

    # Eventlet signals
    eventlet_pool_started, eventlet_pool_preshutdown,
    eventlet_pool_postshutdown, eventlet_pool_apply,

    # Logging signals
    setup_logging, after_setup_logger, after_setup_task_logger,

    # Command signals
    user_preload_options,

    # Deprecated signals
    task_sent,
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d| %(levelname)-8s| %(process)-5s | %(processName)-18s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


# **Task Signals**
@before_task_publish.connect
def on_before_task_publish(headers=None, body=None, **kwargs):
    logger.info("before_task_publish: headers=%s, body=%s", headers, body)


@after_task_publish.connect
def on_after_task_publish(sender=None, **kwargs):
    logger.info("after_task_publish: sender=%s", sender)


@task_prerun.connect
def on_task_prerun(task_id=None, task=None, **kwargs):
    logger.info("task_prerun: task_id=%s, task=%s", task_id, task)


@task_postrun.connect
def on_task_postrun(task_id=None, task=None, **kwargs):
    logger.info("task_postrun: task_id=%s, task=%s", task_id, task)


@task_retry.connect
def on_task_retry(request=None, reason=None, **kwargs):
    logger.info("task_retry: request=%s, reason=%s", request, reason)


@task_success.connect
def on_task_success(result=None, **kwargs):
    logger.info("task_success: result=%s", result)


@task_failure.connect
def on_task_failure(task_id=None, exception=None, **kwargs):
    logger.info("task_failure: task_id=%s, exception=%s", task_id, exception)


@task_internal_error.connect
def on_task_internal_error(task_id=None, exception=None, **kwargs):
    logger.info("task_internal_error: task_id=%s, exception=%s", task_id, exception)


@task_received.connect
def on_task_received(request=None, **kwargs):
    logger.info("task_received: request=%s", request)


@task_revoked.connect
def on_task_revoked(request=None, **kwargs):
    logger.info("task_revoked: request=%s", request)


@task_unknown.connect
def on_task_unknown(name=None, id=None, **kwargs):
    logger.info("task_unknown: name=%s, id=%s", name, id)


@task_rejected.connect
def on_task_rejected(name=None, id=None, **kwargs):
    logger.info("task_rejected: name=%s, id=%s", name, id)


# **App Signals**
@import_modules.connect
def on_import_modules(*args, **kwargs):
    logger.info("01 import_modules: args=%s", args)


# **Worker Signals**
@celeryd_after_setup.connect
def on_celeryd_after_setup(sender=None, instance=None, **kwargs):
    logger.info("celeryd_after_setup: sender=%s, instance=%s", sender, instance)


@celeryd_init.connect
def on_celeryd_init(**kwargs):
    logger.info("celeryd_init")


@worker_init.connect
def on_worker_init(**kwargs):
    logger.info("worker_init")


@worker_before_create_process.connect
def on_worker_before_create_process(**kwargs):
    logger.info("worker_before_create_process")


@worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info("worker_ready")


@heartbeat_sent.connect
def on_heartbeat_sent(**kwargs):
    pass
    logger.info("heartbeat_sent")


@worker_shutting_down.connect
def on_worker_shutting_down(**kwargs):
    logger.info("worker_shutting_down")


@worker_process_init.connect
def on_worker_process_init(**kwargs):
    logger.info("worker_process_init")


@worker_process_shutdown.connect
def on_worker_process_shutdown(**kwargs):
    logger.info("worker_process_shutdown")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    logger.info("worker_shutdown")


# **Beat Signals**
@beat_init.connect
def on_beat_init(**kwargs):
    logger.info("beat_init")


@beat_embedded_init.connect
def on_beat_embedded_init(**kwargs):
    logger.info("beat_embedded_init")


# **Eventlet Signals**
@eventlet_pool_started.connect
def on_eventlet_pool_started(**kwargs):
    logger.info("eventlet_pool_started")


@eventlet_pool_preshutdown.connect
def on_eventlet_pool_preshutdown(**kwargs):
    logger.info("eventlet_pool_preshutdown")


@eventlet_pool_postshutdown.connect
def on_eventlet_pool_postshutdown(**kwargs):
    logger.info("eventlet_pool_postshutdown")


@eventlet_pool_apply.connect
def on_eventlet_pool_apply(**kwargs):
    logger.info("eventlet_pool_apply")


# **Logging Signals**
@setup_logging.connect
def on_setup_logging(**kwargs):
    logger.info("setup_logging")


@after_setup_logger.connect
def on_after_setup_logger(**kwargs):
    logger.info("after_setup_logger")


@after_setup_task_logger.connect
def on_after_setup_task_logger(**kwargs):
    logger.info("after_setup_task_logger")


# **Command Signals**
@user_preload_options.connect
def on_user_preload_options(options=None, **kwargs):
    logger.info("user_preload_options: options=%s", options)


# **Deprecated Signals**
@task_sent.connect
def on_task_sent(sender=None, **kwargs):
    logger.info("task_sent: sender=%s", sender)


@app.task
def test_task() -> None:
    logger.info('task 1...')
