from django import forms
from django.core.validators import MinValueValidator

from typing import Any

from restaurants.models import ItemVariation, Order

class OrderForm(forms.Form):
    type_choices = (
        ("d", "delivery"),
        ("i", "dine-in")
    )
    order_type = forms.ChoiceField(choices=type_choices,
                                   initial="i")
 

class OrderEditForm(OrderForm):
    public_uuid = forms.UUIDField()
    
    def clean(self, *args, **kwargs):
        public_uuid = self.cleaned_data.get("public_uuid")
        if not Order.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError({
                "public_uuid": "Nothing was found with this identifier."})
        return super().clean(*args, **kwargs)
    
    
class DineInForm(forms.Form):
    table_number = forms.IntegerField(min_value=1,
                                      widget=forms.NumberInput(attrs={
                                          "class": "dinein_table_num form-control text-light",
                                          "id": "dinein_table_num"}))
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "dinein_desc form-control text-light",
                "id": "dinin_desc"}))
    

class OrderDeleteForm(forms.Form):
    public_uuid = forms.UUIDField()
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        
        if not Order.objects.filter(public_uuid=public_uuid).exists():
            self.add_error({"public_uuid": "no such order was found."})
            raise forms.ValidationError({"public_uuid": "the given uuid was invalid."})
        
        return cleaned_data
    

class OrderItemForm(forms.Form):
    count = forms.IntegerField(validators=[MinValueValidator(0)],
                               label="",
                               required=False,
                               widget=forms.NumberInput(attrs={
                                   "class": "form-control item-count px-1 mt-1 px-1"}))
    item = forms.ModelChoiceField(to_field_name="public_uuid",
                                  queryset=ItemVariation.objects.none(),
                                  disabled=True,
                                  label="",
                                  widget=forms.Select(attrs={
                                      "class": "form-control mt-1 px-1"}))
    fee = forms.IntegerField(validators=[MinValueValidator(0)],
                             disabled=True,
                             required=False,
                             widget=forms.NumberInput(attrs={
                                 "class": "form-control fee mt-1 px-1"}))
    auto_price = forms.BooleanField(label="",
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={
                                        "class": "auto-price form-check-input"}))
    paid_price = forms.IntegerField(label="",
                                    required=False,
                                    widget=forms.NumberInput(attrs={
                                        "class": "form-control paid-price mt-1 px-1"}))
    
    def __init__(self, 
                 item_qs:ItemVariation=ItemVariation.objects.none(),
                 *args, 
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = item_qs
        
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        print(cleaned_data)
        if cleaned_data.get("paid_price") is None:
            cleaned_data["paid_price"] = (self.initial.get("paid_price") 
                                          or 0)
        if cleaned_data.get("auto_price") is None:
            cleaned_data["auto_price"] = (self.initial.get("auto_price") 
                                          or True)
        if cleaned_data.get("count") is None:
            cleaned_data["count"] = (self.initial.get("count") 
                                     or 0)
        return cleaned_data
