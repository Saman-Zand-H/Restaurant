from django import template
from decimal import Decimal


register = template.Library()


@register.filter
def qs_exists(reverse_desc, manager_name="objects"):
    return reverse_desc(manager=manager_name).within().exists()


@register.filter
def reverse_manager_using(reverse_desc, manager_name="objects"):
    return reverse_desc(manager=manager_name).within()

@register.filter
def trunc_number(val):
    if val // 1000 == 0:
        return val
    elif val // 1000 < 1000:
        return f"{val//1000}k"
    else:
        return f"{val//10**5/10}m"
    