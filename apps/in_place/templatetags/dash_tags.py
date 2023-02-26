from django import template

from users.models import UserModel


register = template.Library()

@register.filter
def qs_exists(reverse_desc, manager_name="objects"):
    return reverse_desc(manager=manager_name).within().exists()


@register.filter
def reverse_manager_using(reverse_desc, manager_name="objects"):
    return reverse_desc(manager=manager_name).within()


@register.filter
def trunc_number(val:str|int):
    assert isinstance(val, int) or (isinstance(val, str) and val.isdigit())
    if isinstance(val, str):
        val = int(val)
    
    len_number = len(str(val)) - 1
    pow_10 = len_number // 3
        
    prefix = ""
    match pow_10:
        case 0:
            pass
        case 1:
            prefix = "k"
        case 2:
            prefix = "m"
        case 3:
            prefix = "b"
        case 4:
            prefix = "kb"
    
    return f"{val//pow(10, 3*pow_10)}{prefix.upper()}"
    

@register.filter
def check_perm(user:UserModel, code_name:str):
    return user.has_perm(code_name)
