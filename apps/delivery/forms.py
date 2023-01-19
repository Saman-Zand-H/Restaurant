from django import forms

from .models import UserAddressInfo


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


class LocationForm(forms.Form):
    address = forms.ChoiceField(choices=[])
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["address"].choices = ((i["public_uuid"], i["address"]) 
                                          for i in user.user_addresses.values("public_uuid", "address"))
        
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        address = cleaned_data["address"]
        if (address_qs:=UserAddressInfo.objects.filter(public_uuid=address)).exists():
            cleaned_data["address"] = address_qs.first()
            return cleaned_data
        self.add_error("address", "No record found.")
        raise forms.ValidationError("Invalid uuid for address.")
