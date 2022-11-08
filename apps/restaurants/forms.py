from django import forms
        

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
