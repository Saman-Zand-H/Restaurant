from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

class AddItemToCartForm(forms.Form):
    public_uuid = forms.UUIDField(required=False)
    
class SetItemCountForm(forms.Form):
    op_choices = (
        ("i", "increase"),
        ("d", 'decrease'),
    )
    op = forms.ChoiceField(choices=op_choices,
                           required=False)
    public_uuid = forms.UUIDField(required=False)


class DiscountForm(forms.Form):
    op_choices = (
        ("a", "add"),
        ("d", "delete"),
    )
    promo_code = forms.CharField(max_length=20)
    op = forms.ChoiceField(choices=op_choices)
