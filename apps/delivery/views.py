from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.db.models import F
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from functools import partial
from datetime import datetime
from asgiref.sync import sync_to_async

from .models import DeliveryCart, DeliveryCartItem, Discount
from restaurants.models import ItemVariation
from .forms import AddItemToCartForm, SetItemCountForm, DiscountForm


class AddToCartView(View, LoginRequiredMixin):
    def post(self, *args, **kwargs):
        form_data = AddItemToCartForm(self.request.POST)
        if form_data.is_valid():
            cart, _ = DeliveryCart.objects.get_or_create(user=self.request.user,
                                                         paid=False)
            item_var = ItemVariation.objects.filter(
                public_uuid=form_data.cleaned_data.get("public_uuid"))
            if item_var.exists():
                _, created = DeliveryCartItem.objects.get_or_create(
                    cart=cart,
                    item=item_var.first(),
                    count=1)
                if created:
                    message = "Item was added to your cart."
                else:
                    message = "Item was already present in your cart."
                return JsonResponse({
                    "user_cart_count": self.request.user.user_cart.cart_items.count(),
                    "message": message,
                    "message_tag": "success" if created else "info",
                })
                
            else:
                messages.warning(self.request, 
                                 "No valid item was retrieved by us.")
                return HttpResponseBadRequest()
                
                
add_to_cart_view = AddToCartView.as_view()


class CartView(View):
    template_name = "delivery/cart.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        return render(self.request, self.template_name, self.context)
    
    def post(self, *args, **kwargs):
        form_data = SetItemCountForm(self.request.POST)
        if form_data.is_valid():
            op = form_data.cleaned_data.get("op")
            public_uuid = form_data.cleaned_data.get("public_uuid")
            cart_item = DeliveryCartItem.objects.filter(public_uuid=public_uuid)
            if cart_item.exists():
                cart_item = cart_item.first()
                if op == "i":
                    cart_item.count = F("count") + 1
                    cart_item.save()
                    return HttpResponse(content="incremented.")
                else:
                    count = cart_item.count
                    if count > 1:
                        cart_item.count = F("count") - 1
                        cart_item.save()
                        return HttpResponse(content="decremented.")
                    cart_item.delete()
                    return HttpResponse(content="deleted.")
            else:
                return HttpResponseBadRequest("item does not exists.")
        else:
            return HttpResponseBadRequest(
                content="invalid form detected.")

cart_view = CartView.as_view()


class DiscountView(View):
    def post(self, *args, **kwargs):
        form_data = DiscountForm(self.request.POST)
        if form_data.is_valid():
            op = form_data.cleaned_data.get("op")
            promo_code = form_data.cleaned_data.get("promo_code")
            promo_obj = Discount.objects.filter(discount_code=promo_code)
            match op:
                case "a":
                    if promo_obj.exists():
                        try:
                            promo_obj = promo_obj.first()
                            if (promo_obj.expiration_date is None  
                                or datetime.now().isoformat() < promo_obj.expiration_date.isoformat()):
                                self.request.user.user_cart.discounts.add(promo_obj)
                                messages.success(self.request, "Discount was added to your cart.")
                            else:
                                messages.error(self.request, "This promo code is expired.")
                        except ValidationError:
                            messages.error(self.request, 
                                        "You can't have multiple_discounts for the same item.")
                    else:
                        messages.error(self.request, "This promo code does not exist.")
                    return redirect("delivery:cart")
                case "d":
                    if promo_obj.exists():
                        self.request.user.user_cart.discounts.remove(
                            promo_obj.first())
                    return redirect("delivery:cart")
        messages.warning(self.request, "Invalid input was provided.")   
        return redirect("delivery:cart")
            
            
discount_view = DiscountView.as_view()       
