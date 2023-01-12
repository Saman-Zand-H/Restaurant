from django import forms

from phonenumber_field.formfields import PhoneNumberField

from .models import RestaurantType
        

class FilterItems(forms.Form):
    name = forms.CharField(required=False,
                           widget=forms.TextInput(
                               attrs={"placeholder": "item or restaurant name",
                                      "id": "itemName",
                                      "class": "border border-1 px-2 rounded-lg mb-3 mx-auto"}),
                           label="")
    is_open = forms.BooleanField(required=False,
                                 widget=forms.CheckboxInput(attrs={
                                     "class": "form-check-input ms-auto mt-1 mx-auto",
                                     "id": "isOpenField"}))
    free_delivery = forms.BooleanField(required=False,
                                       widget=forms.CheckboxInput(attrs={
                                     "class": "form-check-input ms-auto mt-1 mx-auto",
                                     "id": "freeDeliveryField"}))
    price = forms.DecimalField(required=False,
                               max_digits=7,
                               decimal_places=3)
    score = forms.IntegerField(required=False,
                               min_value=1, 
                               max_value=5)
    page = forms.IntegerField(required=False, min_value=1)
    
    
class FilterRestaurants(forms.Form):
    name = forms.CharField(required=False,
                           widget=forms.TextInput(
                               attrs={"placeholder": "restaurant name",
                                      "id": "itemName",
                                      "class": "border border-1 px-2 rounded-lg mb-3 mx-auto"}),
                           label="")
    is_open = forms.BooleanField(required=False,
                                 widget=forms.CheckboxInput(attrs={
                                     "class": "form-check-input ms-auto mt-1 mx-auto",
                                     "id": "isOpenField"}))
    free_delivery = forms.BooleanField(required=False,
                                       widget=forms.CheckboxInput(attrs={
                                     "class": "form-check-input ms-auto mt-1 mx-auto",
                                     "id": "freeDeliveryField"}))
    score = forms.IntegerField(required=False,
                               min_value=0, 
                               max_value=5)
    page = forms.IntegerField(required=False,
                              min_value=1,
                              max_value=5)
    lat = forms.FloatField(required=False)
    lon = forms.FloatField(required=False)
    op_type = forms.CharField(required=False)
    type = forms.CharField(required=False)


class NewPartnerForm(forms.Form):
    roles_choices = (
        ("ca", "cashier"),
        ("ch", "chef"),
        ("s", "supplier"),
        ("w", "waiter"),
        ("m", "manager"),
        ("d", "driver"),
    )
    restaurant_type_choices = (
        (i["id"], i["name"])
        for i in RestaurantType.objects.values("id", "name")
    )
    
    role = forms.ChoiceField(initial="m",
                             choices=roles_choices,
                             label="Your Role",
                             widget=forms.RadioSelect())
    name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "the name of your restaurant, e.g. McDonald etc.",
    }))
    opens_at = forms.TimeField(widget=forms.TextInput(attrs={"id": "opens_at"}))
    closes_at = forms.TimeField(widget=forms.TextInput(attrs={"id": "closes_at"}))
    # todo: handle 24h restaurants
    description = forms.CharField(required=False,
                                  widget=forms.Textarea())
    restaurant_type = forms.ChoiceField(choices=restaurant_type_choices,
                                        widget=forms.RadioSelect())
    phone_number = PhoneNumberField(required=False)
    table_count = forms.IntegerField(min_value=0)
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        restaurant_type = cleaned_data.get("restaurant_type")
        cleaned_data["restaurant_type"] = RestaurantType.objects.get(id=restaurant_type)
        return cleaned_data
