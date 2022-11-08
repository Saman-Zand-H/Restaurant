import os
from datetime import time
from logging import getLogger
from typing import List

from django.core.exceptions import ValidationError
from django.core.paginator import (Paginator, PageNotAnInteger, 
                                   EmptyPage, InvalidPage)


logger = getLogger(__name__)

def validate_extension(file):
    ext = os.path.splitext(file.name)[1]
    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
    if not ext.lower() in valid_exts:
        logger.info(f"Invalid file extension: {file.name}")
        raise ValidationError("Forbidden file extenstion."
                              f" Valid file extensions are as following: {valid_exts}")
        
        
def validate_size(file):
    if file.size >= 6 * 1024 ** 2:
        logger.info(f"Invalid file size: {file.size}")
        raise ValidationError(
            " Invalid file size. File size cannot exceed 6mb.")
        
        
def validate_isoformat(value: str):
    try:
        time.fromisoformat(value.replace("Z", "+00:00"))
    except:
        raise ValidationError("Invalid date format."
                              " Please use the following format: HH:MM:SS")
        

def get_paginator_page(paginator, page):
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)
    except InvalidPage:
        results = paginator.page(1)
    return results


def paginate(page, pag_object, obj_per_page):
    paginator = Paginator(pag_object, obj_per_page)
    results = get_paginator_page(paginator, page)
    return (results, paginator)

