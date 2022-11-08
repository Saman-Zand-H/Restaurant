from django.shortcuts import render, redirect
from django.forms import formset_factory
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction, IntegrityError
from django.views import View

from logging import getLogger
from typing import NamedTuple

from .utils import (weekly_revenue_chart_data, 
                    weekly_sale_chart_data, 
                    weekly_score_chart_data)
from .forms import (OrderForm, 
                    OrderItemForm, 
                    OrderEditForm, 
                    OrderDeleteForm, 
                    DineInForm)
from .models import DineInOrder
from restaurants.models import (ItemVariation, 
                                Order, 
                                OrderItem, 
                                Restaurant)


logger = getLogger(__name__)


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/dashboard.html"
    context = dict()
    
    def test_func(self):
        return hasattr(self.request.user, "user_staff")
     
    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        score_chart, revenue_chart, sale_chart = (
            weekly_score_chart_data(restaurant.weekly_score),
            weekly_revenue_chart_data(
                [i//1000 for i in restaurant.weekly_revenue]),
            weekly_sale_chart_data(restaurant.weekly_sale))
        item_var_qs = ItemVariation.objects.filter(
            item__cuisine__restaurant=restaurant)
        OrderItemFormset = formset_factory(OrderItemForm,
                                           extra=item_var_qs.count(),
                                           max_num=item_var_qs.count())
        session_form_vals = self.get_forms_from_session()
        order_form, dinein_form, order_item_formset = (
            session_form_vals.get("order_form") or OrderForm(),
            session_form_vals.get("dinein_form") or DineInForm(),
            session_form_vals.get("order_item_formset") 
                or OrderItemFormset(
                                 form_kwargs={"item_qs": item_var_qs},
                                 initial=[
                                     {"count": 0, "item": i, "fee": i.price or 0} 
                                      for i in item_var_qs]
                                 ))
        self.context.update({"score_chart": score_chart,
                             "revenue_chart": revenue_chart,
                             "sale_chart": sale_chart,
                             "restaurant": restaurant,
                             "orders": self.prepare_order_namedtuple(restaurant),
                             "order_form": order_form,
                             "dinein_form": dinein_form,
                             "order_item_formset": order_item_formset})
        return render(self.request, self.template_name, self.context)
    
    def post(self, *args, **kwargs):
        order_form_data = OrderForm(self.request.POST)
        try:
            with transaction.atomic():
                if order_form_data.is_valid():
                    restaurant = self.request.user.user_staff.restaurant
                    order_type = order_form_data.cleaned_data.get("order_type")
                    item_var_qs = ItemVariation.objects.filter(
                        item__cuisine__restaurant=restaurant)
                    OrderItemFormset = formset_factory(
                        OrderItemForm,
                        extra=item_var_qs.count(),
                        max_num=item_var_qs.count())
                    response = self.handle_formset_create(
                        OrderItemFormset, 
                        item_var_qs, 
                        order_type,
                        restaurant)
                    return response
        except (ValidationError, IntegrityError):
            return self.render_or_redirect()
                     
    def handle_formset_create(self, 
                              formset, 
                              item_var_qs, 
                              order_type, 
                              restaurant):
        formset_data = formset(self.request.POST,
                               initial=[
                                  {
                                      "count": 0, 
                                      "item": i, 
                                      "fee": i.price
                                   } 
                                   for i in item_var_qs],
                               form_kwargs={
                                   "item_qs": item_var_qs})
        if formset_data.is_valid():
            order = Order.objects.create(restaurant=restaurant,
                                         order_type=order_type)
            if order_type == "i":
                dinein_form = DineInForm(self.request.POST)
                if dinein_form.is_valid():
                    d_cleaned = dinein_form.cleaned_data
                    # At this point, if the data provided isn't valid,
                    # we're gonna have a callback, which since we're using
                    # an atomic transaction here will make a complete rollback
                    self._validate_table_number(order, 
                                                d_cleaned.get("table_number"), 
                                                dinein_form)
                    DineInOrder.objects.create(
                        table_number=d_cleaned.get("table_number"),
                        description=d_cleaned.get("description"),
                        order=order)
                else:
                    self.request.session["dinein_form"] = dinein_form
                    messages.error(self.request,
                                   "Invalid data was provided. Try again.") 
                    raise ValidationError(f"Form validation failed {dinein_form.errors}")
            filled_forms = [*filter(lambda x: x.cleaned_data.get("count"), 
                                    formset_data.forms)]
            OrderItem.objects.bulk_create(
                [OrderItem(
                    item=i.cleaned_data.get("item"),
                    order=order,
                    count=i.cleaned_data.get("count"),
                    paid_price=(
                        i.cleaned_data.get("paid_price") 
                        if not i.cleaned_data.get("auto_price") 
                        else i.cleaned_data.get("item").price
                            * i.cleaned_data.get("count")))
                for i in filled_forms]
            )
            messages.success(self.request, 
                             "Order was submitted successfully.")
            return redirect("in_place:dashboard")
        messages.error(self.request,
                       "Order was not submitted. We recognized invalid inputs here.")
        self.context.update({"order_item_formset": formset_data})
        return self.render_or_redirect() 
        
    def prepare_order_namedtuple(self, restaurant):
        item_var_qs = ItemVariation.objects.filter(
            item__cuisine__restaurant=restaurant)
        OrderItemFormset = formset_factory(
            OrderItemForm,
            extra=item_var_qs.count(),
            max_num=item_var_qs.count())
        
        class OrderData(NamedTuple):
            formset: OrderItemFormset
            qs: Order
            order_form: OrderEditForm
            dinein_form: DineInForm = None
            
        def formset_initials(order):
            items = ItemVariation.objects.filter(
                item_orders__in=order.order_items.all())
            item_diff = item_var_qs.difference(items)
            order_items = [
                {
                    "count": i.count,
                    "item": i.item,
                    "fee": i.item.price or 0,
                    "paid_price": i.paid_price or 0
                } for i in order.order_items.all()]
            empty_items =[{"count": 0, "item": i, "fee": i.price or 0, "paid_price": 0} 
                            for i in item_diff]
            return order_items + empty_items
            
        orders = restaurant.restaurant_orders.all()
        data = [
            OrderData(
                qs=order,
                formset=OrderItemFormset(
                    form_kwargs={"item_qs": item_var_qs,
                                 "auto_id": f"edit_%s-{order.public_uuid}"},
                    initial=formset_initials(order)),
                order_form=OrderEditForm(
                    initial={
                        "order_type": order.order_type
                    }),
                dinein_form=DineInForm(initial={
                    "table_number": order.order_dinein.table_number,
                    "description": order.order_dinein.description}) 
                    if order.order_type == "i" else None)
            for order in orders]
        return data
    
    def _validate_table_number(self, order, table_number, form_data):
        if table_number > order.restaurant.table_count:
            form_data.add_error(
                "table_number",  
                f"Table number exceeded the total number of the tables({order.restaurant.table_count}).")
            messages.error(self.request, 
                           "Order was not submitted. We recognized an invalid input.")
            self.context.update({"dinein_form": form_data})
            
    def get_forms_from_session(self):
        keys = ["order_form", "dinein_form"]
        vals = [self.request.session.get(i) for i in keys]
        cleaned = [*filter(lambda x: x[1], zip(keys, vals))]
        return {i[0]: i[1] for i in cleaned}
            
    def render_or_redirect(self):
        if len(self.context.keys()) == 8:
            return render(self.request, self.template_name, self.context)
        return redirect("in_place:dashboard")
    
    
dashboard_view = DashboardView.as_view()    


class EditOrderView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, "user_staff")
    
    def get(self, *args, **kwargs):
        return redirect("in_place:dashboard")
    
    def post(self, *args, **kwargs):
        order_data = OrderEditForm(self.request.POST)
        with transaction.atomic():
            if order_data.is_valid():
                order = Order.objects.get(
                    public_uuid=order_data.cleaned_data.get("public_uuid"))
                
                if order.order_type == "i":
                    dinein_form = DineInForm(self.request.POST,
                                            initial={
                                                "table_number": order.order_dinein.table_number,
                                                "description": order.order_dinein.description})
                    if dinein_form.is_valid() and dinein_form.has_changed():
                        DineInOrder.objects.select_for_update().filter(
                            order__public_uuid=order.public_uuid).update(
                                table_number=dinein_form.cleaned_data.get("table_number"),
                                description=dinein_form.cleaned_data.get("description"))
                    elif not dinein_form.is_valid():
                        self.request.session["dinein_form"] = dinein_form
                        self._invalid_input_message()
                        return redirect("in_place:dashboard")
                    
                order_item_qs = order.order_items.all()
                item_var_qs = ItemVariation.objects.filter(
                    item__cuisine__restaurant=order.restaurant)
                items_diff = item_var_qs.difference(
                    ItemVariation.objects.filter(item_orders__in=order_item_qs))
                OrderItemFormset = formset_factory(OrderItemForm,
                                                   extra=order_item_qs.count(),
                                                   max_num=order_item_qs.count())
                formset_data = OrderItemFormset(self.request.POST,
                                                form_kwargs={"item_qs": item_var_qs},
                                                initial=[
                                                    {
                                                        "count": i.count, 
                                                        "item": i.item, 
                                                        "fee": i.item.price,
                                                        "paid_price": i.paid_price,
                                                        "auto_price": 1,
                                                    } for i in order_item_qs]
                                                    + [
                                                        {
                                                            "count": 0,
                                                            "item": i,
                                                            "fee": i.price,
                                                            "paid_price": 0,
                                                            "auto_price": 1
                                                        } for i in items_diff
                                                    ])
                if formset_data.is_valid():
                    formset_forms = [*formset_data.forms]
                    changed_forms = [*filter(lambda x: x.has_changed(), 
                                            formset_forms)]
                    for form in changed_forms:
                        item = form.cleaned_data.get("item")
                        paid = form.cleaned_data.get("paid_price")
                        auto = form.cleaned_data.get("auto_price")
                        count = form.cleaned_data.get("count")
                        fee = item.price
                            
                        order.order_items.select_for_update().filter(
                            item=item).update(
                                count=count,
                                paid_price=paid if not auto else count*fee)
                    messages.success(self.request, 
                                    "The Order was updated successfully.")
                else:
                    print(formset_data.errors)
                    self._invalid_input_message()
                return redirect("in_place:dashboard")
            
        self.request.session["order_form"] = order_data
        self.request.session["order_item_formset"] = formset_data
        self._invalid_input_message()
        return redirect("in_place:dashboard")
        
    def _invalid_input_message(self):
        return messages.error(self.request,
                             "Invalid data was provided. Try again.")
        
        
edit_order_view = EditOrderView.as_view()


class DeleteOrderView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff") 
                and self.request.user.has_perm("delte_orders"))
    
    def post(self, *args, **kwargs):
        form_data = OrderDeleteForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            Order.objects.filter(public_uuid=public_uuid).delete()
            messages.success(self.request,
                             "Order was deleted successfully.")
        else:
            messages.error(self.request, 
                           "No such order was found. If you sure " 
                           "you didn't do anything wrong contact our support.")
        return redirect("in_place:dashboard")
    

delete_order_view = DeleteOrderView.as_view()
    
    
class OrdersView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/orders.html"
    context = dict()
    
    def test_func(self):
        return hasattr(self.request.user, "user_staff")
    
    def get(self, *args, **kwargs):
        pass
    