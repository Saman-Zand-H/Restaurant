from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos.point import Point
from django.http import HttpResponse
from django.db import transaction


from delivery.models import UserAddressInfo
from .forms import AddressForm, EditAddressForm, EditAddressRequestForm


class ProfileView(View, LoginRequiredMixin):
    template_name = "account/profile.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        self.context.update({
            "sidebar": "user",
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


class DashboardView(View):
    template_name = "account/dashboard.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        return render(self.request, self.template_name, self.context)
    

dashboard_view = DashboardView.as_view()


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
