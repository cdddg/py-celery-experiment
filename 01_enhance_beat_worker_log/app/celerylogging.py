import logging
from logging import getLogger
from uuid import uuid4

import asgi_correlation_id
import colorlog
from asgi_correlation_id.extensions.celery import load_correlation_ids
from celery import Task
from celery.app.trace import LOG_RECEIVED
from celery.signals import after_setup_logger, before_task_publish, task_prerun

from . import SCHEDULED_TASK_NAME_KEY, SCHEDULER_TASK_FLAG_KEY, CELERY_PARENT_ID_KEY

UNSET_ID = ' ' * 8


class IgnoreSpecificLogFilter(logging.Filter):
    def filter(self, record):
        data = getattr(record, 'data', {})

        if record.msg == 'Scheduler: Sending due task %s (%s)':
            return False
        if LOG_RECEIVED % {'name': data.get('name'), 'id': data.get('id')} == record.getMessage():
            return False

        return True


def setup_celery_logging():
    @after_setup_logger.connect(weak=False)
    def on_after_setup_logger(logger, *args, **kwargs):
        correlation_id_filter = asgi_correlation_id.CorrelationIdFilter(
            uuid_length=8, default_value=UNSET_ID
        )
        celery_tracing_filter = asgi_correlation_id.CeleryTracingIdsFilter(
            uuid_length=8, default_value=UNSET_ID
        )
        ignore_specific_log_filter = IgnoreSpecificLogFilter()

        formatter = colorlog.ColoredFormatter(
            # fmt='%(log_color)s%(levelname)-8s%(reset)s [%(correlation_id)s] [%(celery_parent_id)-8s] [%(celery_current_id)-8s] %(name)-22s | %(log_color)s%(message)s%(reset)s',
            fmt='%(asctime)s.%(msecs)03d| %(log_color)s%(levelname)-8s%(reset)s| %(process)-5s | %(correlation_id)-8s | %(celery_parent_id)-8s | %(celery_current_id)-8s | %(log_color)s%(message)s%(reset)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%',
        )

        handler = colorlog.StreamHandler()
        handler.addFilter(correlation_id_filter)
        handler.addFilter(celery_tracing_filter)
        handler.addFilter(ignore_specific_log_filter)
        handler.setFormatter(formatter)

        logger.handlers.clear()
        logger.addHandler(handler)

    @before_task_publish.connect(weak=False)
    def on_before_task_publish(headers, properties, **kwargs):
        if properties.get(SCHEDULER_TASK_FLAG_KEY) is True:
            # generate a unique UUID and set it as the current correlation_id
            uid = uuid4().hex
            asgi_correlation_id.correlation_id.set(uid)

            # add the correlation_id to the task's headers
            # this ensures that this unique identifier is passed to the celery worker
            headers[load_correlation_ids.__defaults__[0]] = uid

            getLogger(__name__).info(
                'Scheduler: Sending due task %s (%s) in @before_task_publish', properties.get(SCHEDULED_TASK_NAME_KEY),
                headers.get('task')
            )

            # reset the correlation_id
            asgi_correlation_id.correlation_id.set(UNSET_ID)

    @task_prerun.connect(weak=False)
    def on_task_prerun(task: Task, **kwargs):
        # pylint: disable=logging-not-lazy

        # replace the celery_parent_id with the UNSET_ID if it's not set
        if task.request.get(CELERY_PARENT_ID_KEY) is None:
            asgi_correlation_id.celery_parent_id.set(UNSET_ID)

        msg = LOG_RECEIVED % {'name': task.name, 'id': task.request.id}
        getLogger(__name__).info(
            f'{msg} in in @task_prerun',
            extra={
                'task.name': task.name,
                **{f'task.request.{k}': str(v) for k, v, in vars(task.request).items()}
            }
        )
