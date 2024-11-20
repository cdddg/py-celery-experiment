import os
from datetime import timedelta

from . import SCHEDULED_TASK_NAME_KEY, SCHEDULER_TASK_FLAG_KEY


# common configuration - applies to both celery worker and beat
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = None
enable_utc = True
task_default_queue = 'celery-task-queue'
broker_connection_retry_on_startup = (
    True  # retry broker connections on startup (relevant for celery 6.0+)
)

# worker-specific configuration
worker_redirect_stdouts = False
worker_cancel_long_running_tasks_on_connection_loss = True
worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', 1))

# beat-specific configuration - scheduling of periodic tasks
beat_schedule = {
    'test-nested-job': {
        'task': f'{__package__}.task.first_task',
        'schedule': timedelta(seconds=10),
        'options': {SCHEDULER_TASK_FLAG_KEY: True, SCHEDULED_TASK_NAME_KEY: 'test-nested-job'},
    },
}
beat_schedule_filename = 'celerybeat-schedule'
