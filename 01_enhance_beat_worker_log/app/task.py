import logging

from celery import shared_task

logger = logging.getLogger(__name__)


'''
1st
    -> 2nd
        -> 3rd
            -> 4th
        -> 4th
    -> 2nd
        -> 3rd
            -> 4th
        -> 4th
'''

@shared_task
def first_task() -> None:
    logger.info('Debug task 1')
    second_debug_task.delay()
    second_debug_task.delay()


@shared_task
def second_debug_task() -> None:
    logger.info('Debug task 2')
    third_debug_task.delay()
    fourth_debug_task.delay()


@shared_task
def third_debug_task() -> None:
    logger.info('Debug task 3')
    fourth_debug_task.delay()


@shared_task
def fourth_debug_task() -> None:
    logger.info('Debug task 4')
