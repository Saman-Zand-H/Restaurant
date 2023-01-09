from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy, reverse
from django.views import View
from django.views.generic import FormView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.db import transaction

from allauth.account.forms import ChangePasswordForm
from allauth.account.views import (PasswordChangeView as AllauthChangePasswordView,
                                   EmailView as AllauthEmailView)

from delivery.models import UserAddressInfo
from in_place.forms import EditRestaurantForm
from .forms import (AddressForm, 
                    EditAddressForm, 
                    EditAddressRequestForm, 
                    ChangeUserForm)


class ProfileView(LoginRequiredMixin, View):
    template_name = "account/profile.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        form_kwargs = {"request": self.request}
        session_form_data = self.request.session.pop("auth_form_post", None)
        if session_form_data:
            form_kwargs.update({"data": session_form_data})
        # use the data transmitted through session and then 
        # to regenrate the errors dict validate the data with is_valid()
        change_user_form = ChangeUserForm(**form_kwargs)
        change_user_form.is_valid()
        
        self.context.update({
            "sidebar": "user",
            "change_user_form": change_user_form,
            "change_password_form": ChangePasswordForm(),
            "edit_restaurant_form": EditRestaurantForm(),
            "address_form": AddressForm(),
            "address_form_action": reverse("accounts:add_address")
        })
        return render(self.request, self.template_name, self.context)
    
    def post(self, *args, **kwargs):
        form_data = EditAddressRequestForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            address = self.request.user.user_addresses.filter(public_uuid=public_uuid)
            if address.exists():
                address = address.first()
                self.context.update({"public_uuid": address.public_uuid,
                                     "address_form_action": reverse("accounts:edit_address"),
                                     "address_form": AddressForm(initial={
                    "address": address.address,
                    "location": address.location,
                    "city": address.city,
                    "province": address.province,
                    "postal_code": address.postal_code,
                })})
                return render(self.request, self.template_name, self.context) 
        self.context.update({"address_form": form_data})
        return render(self.request, self.template_name, self.context)

    
profile_view = ProfileView.as_view()
    

class AddAddressView(View):
    context = dict()
    
    def post(self, *args, **kwargs):
        form_data = AddressForm(self.request.POST)
        
        if form_data.is_valid():
            location = form_data.cleaned_data.get("location")
            postal_code = form_data.cleaned_data.get("postal_code")
            address = form_data.cleaned_data.get("address")
            city = form_data.cleaned_data.get("city")
            province = form_data.cleaned_data.get("province")
            
            with transaction.atomic():
                UserAddressInfo.objects.create(
                    user=self.request.user,
                    location=location,
                    address=address,
                    city=city,
                    province=province,
                    postal_code=postal_code,
                )
            return redirect("accounts:profile")
        messages.error(self.request, "Invalid Data entered. "
                                     "Try again and make sure you've set your location on the map.")
        return redirect("accounts:profile")
    
    
add_address_view = AddAddressView.as_view()
    

class EditAddressView(View):
    context = dict()
    
    def post(self, *args, **kwargs):
        form_data = EditAddressForm(self.request.POST)
        
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            address_ins = self.request.user.user_addresses.filter(
                public_uuid=public_uuid)
            
            if address_ins.exists():
                location = form_data.cleaned_data.get("location")
                postal_code = form_data.cleaned_data.get("postal_code")
                address = form_data.cleaned_data.get("address")
                city = form_data.cleaned_data.get("city")
                province = form_data.cleaned_data.get("province")
                address_ins.update(location=location,
                                   postal_code=postal_code,
                                   address=address,
                                   city=city,
                                   province=province)
                self.context["address_form"] = AddressForm()
        return redirect("accounts:profile")

edit_address_view = EditAddressView.as_view()


class DeleteAddressView(View):
    def post(self, *args, **kwargs):
        form_data = EditAddressRequestForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            address = self.request.user.user_addresses.filter(public_uuid=public_uuid)
            if address.exists():
                address.delete()
            else:
                pass
        return redirect("accounts:profile")


delete_address_view = DeleteAddressView.as_view()


class ChangeUserView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        form_data = ChangeUserForm(request=self.request, 
                                   data=self.request.POST)
        if form_data.is_valid() and form_data.has_changed():
            username = self.request.user.username
            changed_data = {i:form_data.cleaned_data.get(i) 
                            for i in form_data.changed_data}
            update_arg_str = ','.join([f'{k}=\'{v}\'' 
                                       for k, v in changed_data.items()])
            exec(f"get_user_model().objects.filter"
                  f"(username='{username}').update({update_arg_str})")
            messages.success(self.request, 
                             "Your informatin was successfully updated.")
        else:
            messages.error(self.request, "Process was not completed. Please try again.")
            # using sessions to show the errors on the template
            self.request.session["auth_form_post"] = form_data.data
        return redirect("accounts:profile")


change_user_view = ChangeUserView.as_view()


class ChangePasswordView(AllauthChangePasswordView):
    def __init__(self, **kwargs):
        super(FormView, self).__init__(**kwargs)
        self.success_url = reverse_lazy("accounts:profile")

    def render_to_response(self, context, **response_kwargs):
        if not self.request.user.has_usable_password():
            return HttpResponseRedirect(reverse("account_set_password"))
        return super().render_to_response(
            context, **response_kwargs
        )
        

change_password_view = ChangePasswordView.as_view()
