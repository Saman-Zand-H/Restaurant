from django import forms
from django.contrib.gis.forms.fields import PointField
from django.contrib.gis.forms.widgets import OSMWidget

from allauth.account.forms import (LoginForm, 
                                   SignupForm as AllauthSignupForm)
from allauth.utils import get_username_max_length
from allauth.account.adapter import get_adapter

from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget


class LoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"].widget = forms.TextInput(
            attrs={
                "class": "form-control px-3", 
                "placeholder": "Your Username",
            },
        )
        self.fields["password"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control px-3",
                "placeholder": "Your Password",
            },
        )
        self.fields["remember"].widget = forms.HiddenInput()


class SignupForm(AllauthSignupForm):
    first_name = forms.CharField(max_length=50,
                                 widget=forms.TextInput(attrs={
                                     "class": "form-control",
                                     "placeholder": "Your First Name",
                                 }))
    last_name = forms.CharField(max_length=50,
                                widget=forms.TextInput(attrs={
                                     "class": "form-control",
                                     "placeholder": "Your Last Name",
                                 }))
    picture = forms.ImageField(label="Picture",
                               required=False,
                               widget=forms.ClearableFileInput(attrs={
                                     "class": "form-control",
                               }))
    phone_number = PhoneNumberField(required=False,
                                    widget=PhoneNumberInternationalFallbackWidget(attrs={
                                        "class": "form-control",
                                    }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = forms.TextInput(attrs={
            "placeholder": "Choose a username",
            "class": "form-control",
            "id": "username",
        })
        self.fields["password1"].widget = forms.PasswordInput(attrs={
                "placeholder": "Choose a password",
                "class": "form-control",
                "id": "password1",
            }
        )
        self.fields["password2"].widget = forms.PasswordInput(attrs={
            "placeholder": "Your password again",
            "class": "form-control",
            "id": "password2",
        })
        self.fields["email"] = forms.EmailField(
            widget=forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. example@example.com",
                }),
            label="E-Mail Address",
        )
    
    
class EditAddressRequestForm(forms.Form):
    public_uuid = forms.UUIDField()
        
        
class AddressForm(forms.Form):
    location = PointField(srid=4326,
                          widget=OSMWidget())
    address = forms.CharField(max_length=255, 
                              widget=forms.TextInput(
                                attrs={"class": "form-control"}))
    postal_code = forms.CharField(max_length=30, 
                              widget=forms.TextInput(
                                attrs={"class": "form-control"}))
    city = forms.CharField(max_length=30, 
                              widget=forms.TextInput(
                                attrs={"class": "form-control"}))
    province = forms.CharField(max_length=30, 
                              widget=forms.TextInput(
                                attrs={"class": "form-control"}))
    
    
class EditAddressForm(AddressForm):
    public_uuid = forms.UUIDField()
    
    
class ChangeUserForm(forms.Form):
    username = forms.CharField(max_length=get_username_max_length(),
                               required=True,
                               widget=forms.TextInput(attrs={
                                   "class": "form-control"
                               }))
    first_name = forms.CharField(max_length=50,
                                 min_length=1,
                                 required=True,
                                 widget=forms.TextInput(attrs={
                                    "class": "form-control"
                                 }))
    last_name = forms.CharField(max_length=50,
                                 min_length=1,
                                 required=True,
                                 widget=forms.TextInput(attrs={
                                    "class": "form-control"
                                 }))
    
    def __init__(self, request=None, *args, **kwargs):
        from collections import deque
        super().__init__(*args, **kwargs)
        if request is not None:
            assert hasattr(request, "user")

            username = request.user.username
            last_name = request.user.last_name
            first_name = request.user.first_name
            
            self.fields["username"].initial = username
            self.fields["last_name"].initial = last_name
            self.fields["first_name"].initial = first_name
                
    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        if "username" in self.changed_data:
            username = self.cleaned_data.get("username")
            get_adapter().clean_username(username)
        return data
