# Celery Signals Execution Order

This document outlines the order of signal execution during the startup of Celery workers, beat, and task lifecycle.

## Worker Startup Signal Order

1. [`import_modules`](https://docs.celeryq.dev/en/stable/userguide/signals.html#import-modules)
2. [`celeryd_init`](https://docs.celeryq.dev/en/stable/userguide/signals.html#celeryd-init)
3. [`worker_init`](https://docs.celeryq.dev/en/stable/userguide/signals.html#worker-init)
4. [`setup_logging`](https://docs.celeryq.dev/en/stable/userguide/signals.html#setup-logging)

   Celery won’t configure the loggers if this signal is connected, so you can use this to completely override the logging configuration with your own.

   If you’d like to augment the logging configuration setup by Celery then you can use the [`after_setup_logger`](https://docs.celeryq.dev/en/stable/userguide/signals.html#std-signal-after_setup_logger) and [`after_setup_task_logger`](https://docs.celeryq.dev/en/stable/userguide/signals.html#std-signal-after_setup_task_logger) signals.
5. [`celeryd_after_setup`](https://docs.celeryq.dev/en/stable/userguide/signals.html#celeryd-after-setup)
6. [`worker_before_create_process`](https://docs.celeryq.dev/en/stable/userguide/signals.html#worker-before-create-process)
7. [`worker_process_init`](https://docs.celeryq.dev/en/stable/userguide/signals.html#worker-process-init)
8. [`worker_ready`](https://docs.celeryq.dev/en/stable/userguide/signals.html#worker-ready)

## Beat Startup Signal Order

1. [`import_modules`](https://docs.celeryq.dev/en/stable/userguide/signals.html#import-modules)
2. [`setup_logging`](https://docs.celeryq.dev/en/stable/userguide/signals.html#setup-logging)

   Celery won’t configure the loggers if this signal is connected, so you can use this to completely override the logging configuration with your own.

   If you’d like to augment the logging configuration setup by Celery then you can use the [`after_setup_logger`](https://docs.celeryq.dev/en/stable/userguide/signals.html#std-signal-after_setup_logger) and [`after_setup_task_logger`](https://docs.celeryq.dev/en/stable/userguide/signals.html#std-signal-after_setup_task_logger) signals.
3. [`beat_init`](https://docs.celeryq.dev/en/stable/userguide/signals.html#beat-init)

## Task Lifecycle Signal Order

1. [`before_task_publish`](https://docs.celeryq.dev/en/stable/userguide/signals.html#before-task-publish) - Triggered before a task is published to the broker.
2. [`after_task_publish`](https://docs.celeryq.dev/en/stable/userguide/signals.html#after-task-publish) - Triggered after a task is published to the broker.
3. [`task_received`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-received) - Triggered when a worker receives a task.
4. [`task_prerun`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-prerun) - Triggered before a task is executed.
5. [`task_success`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-success) - Triggered if a task executes successfully.
6. [`task_retry`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-retry) - Triggered if a task is retried.
7. [`task_failure`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-failure) - Triggered if a task execution fails.
8. [`task_internal_error`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-internal-error) - Triggered if an internal error occurs during task execution.
9. [`task_revoked`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-revoked) - Triggered if a task is revoked.
10. [`task_unknown`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-unknown) - Triggered if a task is unknown.
11. [`task_rejected`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-rejected) - Triggered if a task is rejected.
12. [`task_postrun`](https://docs.celeryq.dev/en/stable/userguide/signals.html#task-postrun) - Triggered after a task is executed, regardless of success or failure.
