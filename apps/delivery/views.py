from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.db.models import F
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from django.views import View

from logging import getLogger
from datetime import datetime
from azbankgateways import (bankfactories, 
                            models as bank_models, 
                            default_settings as settings)
from azbankgateways.exceptions import AZBankGatewaysException

from .models import (DeliveryCart, 
                     DeliveryCartItem, 
                     Discount, 
                     UserAddressInfo)
from .utils import group_delivery_items
from restaurants.models import ItemVariation
from in_place.models import Order, OrderItem
from .forms import (AddItemToCartForm, 
                    SetItemCountForm, 
                    DiscountForm, 
                    LocationForm)


logger = getLogger(__file__)


class AddToCartView(View, LoginRequiredMixin):
    def post(self, *args, **kwargs):
        user = self.request.user
        form_data = AddItemToCartForm(self.request.POST)
        if form_data.is_valid():
            cart_qs = DeliveryCart.objects.filter(user=user)
            
            if (
                not cart_qs.exists()
                or (cart:=cart_qs.latest("date_created")).date_submitted is not None
            ):
                cart = DeliveryCart.objects.create(user=user)
            
            item_var = ItemVariation.objects.filter(
                public_uuid=form_data.cleaned_data.get("public_uuid"))
            
            if (
                item_var.exists() 
                and (location:=item_var.first().item.cuisine.restaurant.location) is not None
            ):
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
            
            elif location is None:
                messages.error(
                    self.request, 
                    "This restaurant doesn't currently support delivery orders."
                )
            
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
            cart_item = DeliveryCartItem.objects.filter(
                public_uuid=public_uuid)
            
            if cart_item.exists():
                cart_item = cart_item.first()
                match op:
                    case "i":
                        cart_item.count = F("count") + 1
                        cart_item.save()
                        return HttpResponse(content="incremented.")
                    case _:
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
                                or datetime.now().isoformat() 
                                    < promo_obj.expiration_date.isoformat()):
                                self.request.user.user_cart.discounts.add(promo_obj)
                                messages.success(self.request, 
                                                 "Discount was added to your cart.")
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


class PurchaseView(LoginRequiredMixin, View):
    result_template_name = ""
    context = dict()
    
    def post(self, *args, **kwargs):
        user = self.request.user
        cart = user.user_cart
        form = LocationForm(data=self.request.POST, user=user)
        cart_qs = DeliveryCart.objects.filter(user=user, id=cart.id)
        
        if not (form.is_valid() or cart.user_address is not None):
            messages.error(self.request, 
                           "Please make sure you have chosen a shipping address.")
            return redirect("delivery:cart")
        elif form.is_valid():
            location = form.cleaned_data["address"]
            cart_qs.update(user_address=location)
            cart = cart_qs.first()
            
        amount = cart.get_estimated_price() * 10
        phone_number = user.phone_number
            
        try:
            bank = bankfactories.BankFactory().auto_create(self.request)
            bank.set_amount(amount)
            bank.set_mobile_number(phone_number)
            bank.set_client_callback_url(
                reverse("delivery:payment_status", args=[cart.public_uuid]))
            payment = bank.ready()
            
            grouped = group_delivery_items(cart.cart_items.all())
            for restaurant, cart_items in grouped:
                description = (f"Order for mr./mrs./miss {user.name.title()}, "
                               f"with phone number: {user.phone_number}, "
                               f"and address: {cart.user_address.address_str}.")
                order = Order.objects.create(restaurant=restaurant,
                                            order_type="d",
                                            cart=cart,
                                            description=description)
                OrderItem.objects.bulk_create([
                    OrderItem(
                        item=i.item,
                        count=i.count,
                        order=order,
                        paid_price=i.item.price*i.count
                    ) for i in cart_items
                ])
                    
            cart_qs.update(date_submitted=timezone.now(),
                           payment=payment,
                           user_address=location)
            
            # create the new cart. This way the cart is refreshed
            # and also we still keep track of previous orders.
            DeliveryCart.objects.create(user=user)
                    
            return bank.redirect_gateway()

        except AZBankGatewaysException as e:
            logger.critical(e, stack_info=True)
            
        return redirect("delivery:payment_status", args=[cart.public_uuid])
        
    
purchase_view = PurchaseView.as_view()


class PurchaseStatusView(LoginRequiredMixin, View):
    template_name = "delivery/payment_status.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        public_uuid = kwargs.get("public_uuid")
        cart_qs = (
            DeliveryCart
            .objects
            .filter(user=self.request.user)
        )
        if (
            public_uuid is not None
            and (cart_qs:=cart_qs.filter(public_uuid=public_uuid)).exists()
            and (cart:=cart_qs.first()).date_submitted is not None
        ):
            self.context.update(
                {
                    "cart": cart
                }
            )
            return render(self.request,
                          self.template_name,
                          self.context)
        messages.error(self.request,
                       "Requested cart is invalid.")
        return redirect("delivery:cart") # todo: change
    

purchase_status_view = PurchaseStatusView.as_view()


class OrdersView(LoginRequiredMixin, View):
    template_name = "delivery/orders.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        self.context.update(
            {
                "carts": (
                    DeliveryCart
                    .objects
                    .filter(user=self.request.user)
                    .exclude(date_submitted=None)
                )
            }
        )
        return render(self.request,
                      self.template_name,
                      self.context)


orders_view = OrdersView.as_view()
