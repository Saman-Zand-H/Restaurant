from celery import shared_task
from celery.utils.log import logger

from .utils import paginate


@shared_task
def paginate_task(page, pag_object, obj_per_page):
    return paginate(page, pag_object, obj_per_page)
    