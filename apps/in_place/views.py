from django.shortcuts import render, redirect
from django.forms import formset_factory
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import (LoginRequiredMixin, 
                                        UserPassesTestMixin)
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.views import View

from datetime import datetime, date, time
from logging import getLogger
from typing import NamedTuple

from .utils import (weekly_revenue_chart_data, 
                    weekly_sale_chart_data, 
                    weekly_score_chart_data)
from .forms import (OrderForm, 
                    OrderItemForm, 
                    OrderEditForm, 
                    OrderDeleteForm, 
                    DineInForm,
                    SearchOrdersForm,
                    CreateStaffForm)
from .models import DineInOrder, Staff
from search_index.es_queries import OrderQuery
from search_index.documents import OrderDocument
from restaurants.models import (ItemVariation, 
                                Order, 
                                OrderItem, 
                                Restaurant)


logger = getLogger(__name__)


def prepare_order_namedtuple(restaurant, timestamp:date=timezone.now().date()):
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
            
    min_t = datetime.combine(timestamp,
                             time.min,
                             timezone.utc)
    max_t = datetime.combine(timestamp,
                             time.max,
                             timezone.utc)
    orders = restaurant.restaurant_orders.filter(
        Q(timestamp__gte=min_t) 
        & Q(timestamp__lte=max_t))
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
                if order.order_type == "i" else DineInForm())
        for order in orders]
    return data


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
                             "orders": prepare_order_namedtuple(restaurant),
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
                    dest = order_form_data.cleaned_data.get("dest")
                    timestamp = order_form_data.cleaned_data.get("timestamp")
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
                        restaurant,
                        dest,
                        timestamp)
                    return response
        except (ValidationError, IntegrityError):
            return self.render_or_redirect()
                     
    def handle_formset_create(self, 
                              formset, 
                              item_var_qs, 
                              order_type, 
                              restaurant,
                              dest, 
                              timestamp=None):
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
            # If provided, use a custom timestamp
            print(timestamp)
            order.timestamp = timestamp
            order.save()
                
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
            return redirect(f"in_place:{dest}")
        messages.error(self.request,
                       "Order was not submitted. We recognized invalid inputs here.")
        self.context.update({"order_item_formset": formset_data})
        return self.render_or_redirect(dest) 
    
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
            
    def render_or_redirect(self, dest="dashboard"):
        if len(self.context.keys()) == 8 and dest != "orders":
            return render(self.request, self.template_name, self.context)
        return redirect(f"in_place:{dest}")
    
    
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
                dest = order_data.cleaned_data.get("dest")
                timestamp = order_data.cleaned_data.get("timestamp")
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
                                description=dinein_form.cleaned_data.get("description"),
                                timestamp=timestamp)
                    elif not dinein_form.is_valid():
                        self.request.session["dinein_form"] = dinein_form
                        self._invalid_input_message()
                        return redirect(f"in_place:{dest}")
                    
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
                            
                        for o in order.order_items.filter(item=item):
                            o.count = count
                            o.paid_price = paid if not auto else count*fee
                            o.save()
                    messages.success(self.request, 
                                    "The Order was updated successfully.")
                else:
                    self._invalid_input_message()
                return redirect(f"in_place:{dest}")
            
        self.request.session["order_form"] = order_data
        self.request.session["order_item_formset"] = formset_data
        self._invalid_input_message()
        return redirect(f"in_place:{dest}")
        
    def _invalid_input_message(self):
        return messages.error(self.request,
                             "Invalid data was provided. Try again.")
        
        
edit_order_view = EditOrderView.as_view()


class DeleteOrderView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff") 
                and self.request.user.has_perm("delete_orders"))
    
    def post(self, *args, **kwargs):
        form_data = OrderDeleteForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            Order.objects.filter(public_uuid=public_uuid).delete()
            messages.success(self.request,
                             "Order was deleted successfully.")
            match form_data.cleaned_data.get("dest"):
                case "orders":
                    return redirect("in_place:orders")
                case _:
                    return redirect("in_place:dashboard")
        else:
            messages.error(self.request, 
                           "No such order was found. If you sure " 
                           "you didn't do anything wrong contact our support.")
        return redirect("in_place:dashboard")
    

delete_order_view = DeleteOrderView.as_view()
    
    
class OrdersView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/orders.html"
    ajax_template_name = "in_place/order_ajax.html"
    modals_ajax_template_name = "in_place/order_modals_ajax.html"
    modals_js_template = "in_place/order_modals_js_ajax.html"
    context = dict()
    class SearchData(NamedTuple):
        order_number: int
        orders_repr: str
        timestamp: datetime
        public_uuid: str
        get_order_type_display: str
    
    def test_func(self):
        return hasattr(self.request.user, "user_staff")
    
    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        order_form, dinein_form, order_item_formset = self.get_modals_context()
        self.context.update({
            "orders": prepare_order_namedtuple(restaurant),
            "order_form": order_form,
            "dinein_form": dinein_form,
            "order_item_formset": order_item_formset,
        })
        return render(self.request, 
                      self.template_name, 
                      self.context)
        
    def post(self, *args, **kwargs):
        form_data = SearchOrdersForm(self.request.POST)
        if form_data.is_valid():
            timestamp = form_data.cleaned_data.get("timestamp", timezone.now().date())
            restaurant = self.request.user.user_staff.restaurant
            query = OrderQuery(restaurant.id, form_data.cleaned_data).query
            e = OrderDocument().search().sort("-timestamp").query(query).execute()
            orders_data = [self.SearchData(
                                order_number=i["_source"]["order_number"],
                                orders_repr=i["_source"]["orders_repr"],
                                timestamp=datetime.fromisoformat(
                                    i["_source"]["timestamp"]),
                                public_uuid=i["_source"]["public_uuid"],
                                get_order_type_display=i["_source"]["get_order_type_display"])
                           for i in e.hits.hits]
            orders_context = {
                "orders": orders_data,
                "daily_revenue": restaurant.get_daily_revenue(timestamp),
            }
            modals_context = {
                "orders": prepare_order_namedtuple(restaurant, timestamp),
            }
            return JsonResponse({"orders_temp": render_to_string(
                                    request=self.request, 
                                    template_name=self.ajax_template_name, 
                                    context=orders_context),
                                 "modals_temp": render_to_string(
                                     request=self.request, 
                                     template_name=self.modals_ajax_template_name, 
                                     context=modals_context),
                                 "modals_js": render_to_string(
                                     request=self.request, 
                                     template_name=self.modals_js_template, 
                                     context=modals_context)})
        return JsonResponse({"error": "Invalid Data Detected."})
    
    def get_forms_from_session(self):
        keys = ["order_form", "dinein_form"]
        vals = [self.request.session.get(i) for i in keys]
        cleaned = [*filter(lambda x: x[1], zip(keys, vals))]
        return {i[0]: i[1] for i in cleaned}
    
    def get_modals_context(self):
        restaurant = self.request.user.user_staff.restaurant
        item_var_qs = ItemVariation.objects.filter(
            item__cuisine__restaurant=restaurant)
        OrderItemFormset = formset_factory(OrderItemForm,
                                           extra=item_var_qs.count(),
                                           max_num=item_var_qs.count())
        session_form_vals = self.get_forms_from_session()
        return (
            session_form_vals.get("order_form") or OrderForm(),
            session_form_vals.get("dinein_form") or DineInForm(),
            session_form_vals.get("order_item_formset") 
                or OrderItemFormset(
                                 form_kwargs={"item_qs": item_var_qs},
                                 initial=[
                                     {"count": 0, "item": i, "fee": i.price or 0} 
                                      for i in item_var_qs]
                                 ))
            
            
orders_view = OrdersView.as_view()
    
class StaffView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/staff.html"
    context = dict()
    
    def test_func(self):
        return (self.request.user.has_perm("in_place.mod_staff")
                and hasattr(self.request.user, "user_staff"))
    
    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        self.context.update({"staff": restaurant.restaurant_staff,
                             "new_form": CreateStaffForm()})
        return render(self.request, self.template_name, self.context)
    
    def post(self, *args, **kwargs):
        form_data = CreateStaffForm(self.request.POST)
        if form_data.is_valid():
            with transaction.atomic():
                user = form_data.save(self.request)
                cleaned_data = form_data.cleaned_data
                
                address = cleaned_data.get("address")
                role = cleaned_data.get("role")
                description = cleaned_data.get("description")
                income = cleaned_data.get("income")
                restaurant = self.request.user.user_staff.restaurant
                try:
                    Staff.objects.create(user=user,
                                         restaurant=restaurant,
                                         address=address,
                                         income=income,
                                         description=description,
                                         role=role)
                    messages.success(self.request, "User was successfully created.")
                    return redirect("in_place:staff")
                except:
                    pass
        print(form_data.errors)
        messages.error(self.request, 
                       "Invalid input detected. Please try again more carefully.")
        self.context.update({"new_form": form_data})
        return render(self.request, self.template_name, self.context)

staff_view = StaffView.as_view()