from django.db import models
from rest_framework.serializers import ValidationError

from typing import List, Tuple


def validate_relations(validated_data:dict,
                       mandatories: List[Tuple[str,str,models.Model]] = [],
                       optionals: List[Tuple[str,str,models.Model]] = []):
    """
    a function to validate date provided to serializers 
       that contain relations.

    Args:
        mandatories: a list of tuples in the format (name, lookup_field, Model)
        optionals: a list of tuples in the format (name, lookup_field, Model)
        validated_data (dict): serializer validate data
    """
    def loop_data(data, required=True):
        for key, field, qs in data:
            assert isinstance(field, str) and isinstance(key, str)
            
            key_field = validated_data.pop(f"{key}_{field}", None)
            if (
                key_field is not None
                and (key_qs:=qs.objects.filter(**{field: key_field})).exists()
            ):
                validated_data[key] = key_qs.first()
            elif required:
                raise ValidationError(f"Required Value '{key}' is not provided.")
        
    loop_data(mandatories)
    loop_data(optionals, False)
    
    return validated_data    
