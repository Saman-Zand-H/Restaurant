from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.contrib.gis.forms import (fields as gis_fields, 
                                      widgets as gis_widgets)
from phonenumber_field.formfields import PhoneNumberField
from iranian_cities.models import Province, City

from abc import abstractmethod

from restaurants.models import ItemVariation, Item, Cuisine
from .models import Staff, Order
from users.forms import SignupForm


class _BaseDeleteForm(forms.Form):
    public_uuid = forms.UUIDField()
    
    @abstractmethod
    def clean(self, *args, **kwargs):
        pass


class OrderForm(forms.Form):
    type_choices = (
        ("d", "delivery"),
        ("i", "dine-in")
    )
    dest_choices = (
        ("orders", "orders"),
        ("dashboard", "dashboard"),
    )
    order_type = forms.ChoiceField(choices=type_choices,
                                   initial="i")
    dest = forms.ChoiceField(choices=dest_choices)
    location = gis_fields.PointField(srid=4326,
                                     disabled=True,
                                     required=False,
                                     widget=gis_widgets.OSMWidget(
                                         attrs={"id": "id_location",
                                                "class": "delivery_location"}
                                     ))
    description = forms.CharField(widget=forms.Textarea(),
                                  required=False)
    timestamp = forms.DateTimeField(required=False,
                                    widget=forms.HiddenInput(attrs={
                                        "id": "newTimestamp"}))
 

class OrderEditForm(OrderForm):
    public_uuid = forms.UUIDField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].widget = gis_widgets.OSMWidget(
            attrs={"id": "id_location_edit", "class": "delivery_location"}
        )
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not Order.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError({
                "public_uuid": "Nothing was found with this identifier."})
        return cleaned_data
    
    
class DineInForm(forms.Form):
    table_number = forms.IntegerField(min_value=1,
                                      widget=forms.NumberInput(attrs={
                                          "class": "dinein_table_num form-control text-light",
                                          "id": "dinein_table_num"}))
    

class OrderDeleteForm(forms.Form):
    dest_choices = (
        ("dashboard", "dashboard"),
        ("orders", "orders"),
    )
    public_uuid = forms.UUIDField()
    dest = forms.ChoiceField(choices=dest_choices)
    
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


class SearchOrdersForm(forms.Form):
    timestamp = forms.DateField()
    keyword = forms.CharField(required=False)


class CreateStaffForm(SignupForm):
    roles_choices = (
        ("ca", "cashier"),
        ("ch", "chef"),
        ("s", "supplier"),
        ("w", "waiter"),
        ("m", "manager"),
    )
    role = forms.ChoiceField(choices=roles_choices,
                             initial="ch",
                             show_hidden_initial=False)
    income = forms.IntegerField(min_value=0,
                                widget=forms.NumberInput(attrs={
                                    "class": "form-control",
                                    "placeholder": "how much are you going to pay?",
                                    "id": "new_income"
                                }))  
    description = forms.CharField(required=False,
                                  widget=forms.Textarea(attrs={
                                      "class": "form-control",
                                      "placeholder": "I take additional context"
                                  }))  
    address = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={
                                  "class": "form-control",
                                  "placeholder": "now where does she/he live"
                              }))
    

class NewCuisineForm(forms.Form):
    name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={
                               "class": "form-control",
                               "placeholder": "What's your cuisine gonna be called?"
                               }),
                           )
    
    
class EditCuisineForm(forms.Form):
    public_uuid = forms.UUIDField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=30)
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not Cuisine.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError({"public_uuid": "This cuisine doesn't exist."})
        return cleaned_data
    
    
class DeleteCuisineForm(_BaseDeleteForm):
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not Cuisine.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError({"public_uuid": "This cuisine doesn't exist."})
        return cleaned_data
    
    
class NewItemForm(forms.Form):
    name = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={
                               "class": "form-control",
                               "placeholder": "What is the name of your item..."
                               }),
                           )
    cuisine = forms.ChoiceField(choices=[],
                                widget=forms.Select(attrs={
                                    "class": "form-control"
                                }))
    picture = forms.ImageField(widget=forms.ClearableFileInput(attrs={
                                        "class": "form-control"
                                    }),
                               required=False,
                               )
    description = forms.CharField(required=False,
                                  widget=forms.Textarea(attrs={
                                            "class": "form-control",
                                            "placeholder": "Is there anything else you want to add..."
                                        }),
                                  )
    
    def __init__(self, cuisine_qs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cuisine"].choices = [
            [i.get("public_uuid"), i.get("name").title()] 
            for i in cuisine_qs
        ]
    
    
class EditItemForm(forms.Form):
    public_uuid = forms.UUIDField()
    name = forms.CharField(max_length=100)
    picture = forms.ImageField(required=False)
    description = forms.CharField(required=False)
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not Item.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError({"public_uuid": "This item doesn't exist."})
        return cleaned_data
    
    
class DeleteItemForm(_BaseDeleteForm):
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not Item.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError({"public_uuid": "This Item Doesn't Exist."})
        return cleaned_data


class NewItemVarForm(forms.Form):
    item = forms.ChoiceField(choices=[], 
                             widget=forms.Select(
                                 attrs={
                                     "class": "form-control"
                                    }
                                ),
                            )
    name = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={
                               "class": "form-control",
                               "placeholder": "What's the name of your item variation..."
                            }),
                           )
    price = forms.IntegerField(validators=[MinValueValidator(0)],
                               widget=forms.NumberInput(
                                   attrs={
                                       "class": "form-control",
                                       "placeholder": "Is it worthy? How much is it?"
                                   }))
    description = forms.CharField(required=False,
                                  widget=forms.Textarea(attrs={
                                            "class": "form-control",
                                            "placeholder": "Is there anything else we should know about?"
                                        }),
                                  )
    
    def __init__(self, item_qs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].choices = [
            [i.get("public_uuid"), i.get("name").title()]
            for i in item_qs
        ]
    
    
class EditItemVarForm(forms.Form):
    public_uuid = forms.UUIDField()
    name = forms.CharField(max_length=100)
    description = forms.CharField(required=False)
    price = forms.IntegerField(validators=[MinValueValidator(0)])
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not ItemVariation.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError(
                {"public_uuid": "This itemvar doesn't exist."})
        return cleaned_data
    
    
class DeleteItemVarForm(_BaseDeleteForm):
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        public_uuid = cleaned_data.get("public_uuid")
        if not ItemVariation.objects.filter(public_uuid=public_uuid).exists():
            raise forms.ValidationError(
                {"public_uuid": "This itemvar doesn't exist."})
        return cleaned_data
    

class StaffUsernameForm(forms.Form):
    username = forms.CharField(max_length=50)
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        username = cleaned_data.get("username")
        assert username is not None
        if not (get_user_model().objects.filter(username=username).exists()
                and Staff.objects.filter(user__username=username).exists()):
            self.add_error("username", "This user doesn't exist or has no staff record. "
                                        "Please don't change the initial data.")
            raise forms.ValidationError("Invalid user detected.",
                                        "invalid_user")
        return cleaned_data


class ChangeStaffForm(forms.Form):
    role_choices = (
        ("ca", "cashier"),
        ("ch", "chef"),
        ("s", "supplier"),
        ("w", "waiter"),
        ("m", "manager"),
        ("d", "driver"),
    )
    role = forms.ChoiceField(choices=role_choices)
    description = forms.CharField(required=False)
    date_created = forms.DateField()
    income = forms.IntegerField(validators=[MinValueValidator(0)])
    address = forms.CharField(required=False)
    phonenumber = PhoneNumberField(required=False)


class EditRestaurantForm(forms.Form):
    name = forms.CharField()
    picture = forms.ImageField(required=False,
                               widget=forms.ClearableFileInput(
                                   attrs={"class": "form-control"}))


class LocationForm(forms.Form):
    province_choices = (
        (i["id"], i["name"]) for i in Province.objects.values("name", "id")
    )
    city_choices = (
        (i["id"], i["name"]) for i in City.objects.values("id", "name")
    )
    
    geo_address = gis_fields.PointField(widget=gis_widgets.OSMWidget(),
                                        srid=4326)
    address = forms.CharField(max_length=255)
    province = forms.ChoiceField(choices=province_choices,
                                 widget=forms.Select())
    city = forms.ChoiceField(choices=city_choices,
                             widget=forms.Select())
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        city = cleaned_data.get("city")
        province = cleaned_data.get("province")
        
        if not (city_qs:=City.objects.filter(id=city)).exists():
            self.add_error("city", "No record of this city was found. Try again.")
            raise forms.ValidationError("Invalid city.")
        if not (province_qs:=Province.objects.filter(id=province)).exists():
            self.add_error("province", "No record of this province was found. Try again.")
            raise forms.ValidationError("Invalid province.")
        
        cleaned_data.update({"province": province_qs.first(),
                             "city": city_qs.first()})
        return cleaned_data
        