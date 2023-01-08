from django.shortcuts import render, redirect
from django.forms import formset_factory
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import (LoginRequiredMixin, 
                                        UserPassesTestMixin)
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.views import View

import json
import xlwt
import numpy as np
from itertools import chain
from functools import reduce
from datetime import datetime, date, time
from logging import getLogger
from typing import NamedTuple

from .utils import (weekly_revenue_chart_data, 
                    weekly_sale_chart_data, 
                    weekly_score_chart_data)
from .utils import sells_gamma, reg_data, orders_geos
from .forms import (OrderForm, 
                    OrderItemForm, 
                    OrderEditForm, 
                    OrderDeleteForm, 
                    DineInForm,
                    SearchOrdersForm,
                    CreateStaffForm,
                    NewCuisineForm,
                    EditCuisineForm,
                    DeleteCuisineForm,
                    NewItemForm,
                    EditItemForm,
                    DeleteItemForm,
                    NewItemVarForm,
                    EditItemVarForm,
                    DeleteItemVarForm)
from .models import DineInOrder, Staff
from search_index.es_queries import OrderQuery
from search_index.documents import OrderDocument
from restaurants.models import (ItemVariation, 
                                Item,
                                Cuisine,
                                Order, 
                                OrderItem, 
                                Restaurant)


logger = getLogger(__name__)


def prepare_order_namedtuple(restaurant, 
                             timestamp:date=timezone.now().date()):
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
        empty_items =[
            {
                "count": 0, "item": i, 
                "fee": i.price or 0, 
                "paid_price": 0
            } 
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
                "table_number": order.order_dinein.table_number 
                    if hasattr("order", "order_dinein") else None,
                "description": order.order_dinein.description
                    if hasattr("order", "order_dinein") else None}) 
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
                    timestamp = order_form_data.cleaned_data.get("timestamp",
                                                                 timezone.now())
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
                              timestamp):
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
                       "Order was not submitted. "
                       "We recognized invalid inputs here.")
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
                try:
                    order = Order.objects.get(
                        public_uuid=order_data.cleaned_data.get("public_uuid"))
                except Order.DoesNotExist:
                    messages.error(self.request, 
                                   "BROKEN OPERATION. Please try again.")
                    return redirect("in_place:dashboard")
                
                if order.order_type == "i":
                    dinein_form = DineInForm(
                        self.request.POST,
                        initial={
                            "table_number": order.order_dinein.table_number
                                if hasattr(order, "order_dine") else None,
                            "description": order.order_dinein.description
                                if hasattr(order, "order_dinein") else None
                        }
                    )
                    if dinein_form.is_valid() and dinein_form.has_changed():
                        # Make sure the object exists
                        DineInOrder.objects.get_or_create(order=order)
                        
                        DineInOrder.objects.select_for_update().filter(
                            order__public_uuid=order.public_uuid).update(
                                table_number=dinein_form.cleaned_data.get("table_number"),
                                description=dinein_form.cleaned_data.get("description"),
                                timestamp=timestamp if timestamp is not None 
                                            else timezone.now())
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
                formset_data = OrderItemFormset(
                    self.request.POST,
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
                        auto = form.cleaned_data.get("auto_price")
                        count = form.cleaned_data.get("count")
                        fee = item.price
                        paid = (count*fee if auto 
                                else form.cleaned_data.get("paid_price", 0))
                        
                        o, _ = OrderItem.objects.get_or_create(order=order,
                                                               item=item)
                        o.count = count
                        o.paid_price = paid
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
            orders_data = [
                self.SearchData(
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
        OrderItemFormset = formset_factory(
            OrderItemForm,
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
                    messages.success(self.request, 
                                     "User was successfully created.")
                    return redirect("in_place:staff")
                except:
                    pass
        messages.error(self.request, 
                       "Invalid input detected. Please try again more carefully.")
        self.context.update({"new_form": form_data})
        return render(self.request, self.template_name, self.context)


staff_view = StaffView.as_view()


class FinanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/fin.html"
    context = dict()
    
    def test_func(self) :
        return (hasattr(self.request.user, "user_staff") 
                and self.request.user.has_perm("in_place.read_finance"))

    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        gamma_data = sells_gamma(restaurant.id)
        regression_data = reg_data(restaurant.id)
        map_data = orders_geos(restaurant.id)
        self.context.update({"gamma_data": json.dumps(gamma_data),
                             "regression_data": json.dumps(regression_data),
                             "map_data": json.dumps(map_data),
                             "mean": round(gamma_data.get("mean"), 3),
                             "median": round(gamma_data.get("med"), 3),
                             "q1": round(gamma_data.get("q1"), 3),
                             "q3": round(gamma_data.get("q3"), 3),
                             "stdev": round(gamma_data.get("stdev"), 3),
                             "mse": round(regression_data.get("mse"), 3),
                             "r2": round(regression_data.get("r2"), 3)})
        return render(self.request, 
                      self.template_name, 
                      self.context)


finance_view = FinanceView.as_view()


class SellsToExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff") 
                and self.request.user.has_perm("in_place.download_fin_data"))
    
    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = (
            "attachment; "
            f"filename={restaurant.name.lower()}_orders.xls")
        
        wb = xlwt.Workbook("utf-8")
        ws = wb.add_sheet("Sell Data (Orders)")
        
        xf = xlwt.XFStyle()
        xf.font.bold = True
        cols = ["items", 
                "timestamp", 
                "paid_price", 
                "order_type", 
                "order_number", 
                "order_id"]
        
        for i in range(len(cols)):
            ws.write(0, i, cols[i], xf)
            
        ############ Orders ############
        qs = Order.objects.filter(restaurant=restaurant).order_by("-timestamp")
        orders_reprs = np.asarray([i.orders_repr for i in qs])
        order_t = np.asarray([i.get_order_type_display() for i in qs])
        total_prices = np.asarray([i.total_price for i in qs])
        fields = [*chain.from_iterable(
            [*qs.values_list("timestamp", "order_number", "id")])]
        timestamp, order_n, order_id = (
            np.asarray(
                [i.isoformat() for i in fields[::3]]), 
            np.asarray(fields[1::3]),
            np.asarray(fields[2::3]))
        data = [
            *reduce(
                lambda i, j: np.append(
                    i, j, axis=1
                    ), 
                [orders_reprs.reshape(-1, 1), 
                 timestamp.reshape(-1, 1), 
                 total_prices.reshape(-1, 1), 
                 order_t.reshape(-1, 1), 
                 order_n.reshape(-1, 1),
                 order_id.reshape(-1, 1)]
            )]
        # Our data now will be in the format [[a0, b0, c0, d0, e0], ...]
        data = [i.tolist() for i in data]
        
        # Enter the order values to the worksheet
        for i, r in enumerate(data):
            print(i, r)
            for d in range(len(r)):
                ws.write(i+1, d, data[i][d])
        
        ############ Order Items ############
        ws = wb.add_sheet("Sell Data (Order Items)")
        qs = OrderItem.objects.filter(order__in=qs).order_by("-timestamp")
        cols = ["item", "count", "paid_price", "order", "timestamp"]
        for i in range(len(cols)):
            ws.write(0, i, cols[i], xf)
        vals = [*chain.from_iterable(
            [*qs.values_list("item", "count", "paid_price", "order", "timestamp")])]
        items, counts, paid_prices, order, timestamp = (
            np.asarray(
                [ItemVariation.objects.get(id=i).full_name 
                 for i in vals[::5]]), 
            np.asarray(vals[1::5]), 
            np.asarray(vals[2::5]),
            np.asarray(vals[3::5]),
            np.asarray([i.isoformat() for i in vals[4::5]]))
        data = [
            *reduce(
                lambda i, j: np.append(
                    i, j, axis=1
                    ), 
                [
                    items.reshape(-1, 1), 
                    counts.reshape(-1, 1), 
                    paid_prices.reshape(-1, 1), 
                    order.reshape(-1, 1),
                    timestamp.reshape(-1, 1)
                ]
            )]
        data = [i.tolist() for i in data]
        
        for i, r in enumerate(data):
            for d in range(len(r)):
                ws.write(i+1, d, data[i][d])
        
        wb.save(response)
        return response
        
    
sells_to_excel_view = SellsToExcelView.as_view()
        
        
class MenuView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/menu.html"
    context = dict()
    
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.read_menu"))
        
    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        cuisines = Cuisine.objects.filter(restaurant=restaurant)
        item_qs = Item.objects.filter(cuisine__restaurant=restaurant)
        
        sessions = self.request.session
        cuisine_form = NewCuisineForm(
            data=sessions.pop("cuisine_form", None))
        item_form = NewItemForm(
            cuisine_qs=cuisines.values("public_uuid", "name"),
            data=sessions.pop("item_form", None))
        itemvar_form = NewItemVarForm(
            item_qs=item_qs.values("name", "public_uuid"),
            data=sessions.pop("itemvar_form", None))
        
        self.context.update({"cuisines": cuisines,
                             "cuisine_form": cuisine_form,
                             "item_form": item_form,
                             "itemvar_form": itemvar_form})
        return render(self.request, self.template_name, self.context)
        
        
menu_view = MenuView.as_view()


class CreateCuisineView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.add_items"))
        
    def post(self, *args, **kwargs):
        form_data = NewCuisineForm(self.request.POST)
        if form_data.is_valid():
            name = form_data.cleaned_data.get("name")
            restaurant = self.request.user.user_staff.restaurant
            Cuisine.objects.create(name=name, restaurant=restaurant)
            messages.success(self.request, 
                             f"{name.title()} was successfully added.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Try again.")
            self.request.session["cuisine_form"] = form_data
        return redirect("in_place:menu")
        
        
create_cuisine_view = CreateCuisineView.as_view()


class EditCuisineView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.edit_items"))
        
    def post(self, *args, **kwargs):
        form_data = EditCuisineForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            name = form_data.cleaned_data.get("name")
            Cuisine.objects.filter(
                public_uuid=public_uuid).update(name=name)
            messages.success(self.request, 
                             "The cuisine was successfully updated.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Try again.")
        return redirect("in_place:menu")
    
    
edit_cuisine_view = EditCuisineView.as_view()


class DeleteCuisineView(LoginRequiredMixin, UserPassesTestMixin, View):    
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.delete_items"))
        
    def post(self, *args, **kwargs):
        form_data = DeleteCuisineForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            Cuisine.objects.filter(
                public_uuid=public_uuid).delete()
            messages.success(self.request, 
                             "The cuisine was successfully deleted.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Try again.")
        return redirect("in_place:menu")
    
    
delete_cuisine_view = DeleteCuisineView.as_view()


class CreateItemView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.add_items"))
        
    def post(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        cuisine_qs = Cuisine.objects.filter(
            restaurant=restaurant).values("public_uuid", "name")
        form_data = NewItemForm(data=self.request.POST, 
                                files=self.request.FILES, 
                                cuisine_qs=cuisine_qs)
        if form_data.is_valid():
            cuisine_uuid = form_data.cleaned_data.get("cuisine")
            cuisine = Cuisine.objects.get(public_uuid=cuisine_uuid)
            picture = form_data.cleaned_data.get("picture")
            name = form_data.cleaned_data.get("name")
            desc = form_data.cleaned_data.get("description")
            Item.objects.create(cuisine=cuisine,
                                name=name,
                                picture=picture,
                                description=desc)
            messages.success(self.request, 
                             f"{name.title()} was successfully added.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Please try again.")
            self.request.session["item_form"] = self.request.POST
        return redirect("in_place:menu")
    
    
create_item_view = CreateItemView.as_view()


class EditItemView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.edit_items"))
        
    def post(self, *args, **kwargs):
        form_data = EditItemForm(
            data=self.request.POST, 
            files=self.request.FILES)
        if form_data.is_valid():
            name = form_data.cleaned_data.get("name")
            desc = form_data.cleaned_data.get("description")
            public_uuid = form_data.cleaned_data.get("public_uuid")
            
            item = Item.objects.get(public_uuid=public_uuid)
            item.name = name
            item.description = desc
            item.picture.delete(save=False)
            item.picture = form_data.files.get("picture")
            item.save()
            
            messages.success(self.request, 
                             f"{name.title()} was successfully updated.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Please try again.")
        return redirect("in_place:menu")
    
    
edit_item_view = EditItemView.as_view()


class DeleteItemView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.delete_items"))
        
    def post(self, *args, **kwargs):
        form_data = DeleteItemForm(self.request.POST, self.request.FILES)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            item = Item.objects.get(public_uuid=public_uuid)
            item.picture.delete(save=True)
            item.delete()
            messages.success(self.request, 
                             f"The item was successfully deleted.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Please try again.")
        return redirect("in_place:menu")
    
    
delete_item_view = DeleteItemView.as_view()


class CreateItemVarView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.add_items"))
        
    def post(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        item_qs = Item.objects.filter(
            cuisine__restaurant=restaurant).values("public_uuid", "name")
        form_data = NewItemVarForm(data=self.request.POST,
                                   item_qs=item_qs)
        if form_data.is_valid():
            item_uuid = form_data.cleaned_data.get("item")
            item = Item.objects.get(public_uuid=item_uuid)
            price = form_data.cleaned_data.get("price")
            description = form_data.cleaned_data.get("description")
            name = form_data.cleaned_data.get("name")
            ItemVariation.objects.create(name=name,
                                         price=price,
                                         item=item,
                                         description=description)
            messages.success(self.request, f"{name.title()} was successfully added.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Please try again.")
            self.request.session["itemvar_form"] = self.request.POST
        return redirect("in_place:menu")
    

create_itemvar_view = CreateItemVarView.as_view()


class EditItemVarView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.edit_items"))
        
    def post(self, *args, **kwargs):
        form_data = EditItemVarForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            name = form_data.cleaned_data.get("name")
            price = form_data.cleaned_data.get("price")
            description = form_data.cleaned_data.get("description")
            ItemVariation.objects.filter(public_uuid=public_uuid).update(
                name=name,
                price=price,
                description=description)
            messages.success(self.request, f"{name.title()} was successfully updated.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Please try again.")
        return redirect("in_place:menu")
    

edit_itemvar_view = EditItemVarView.as_view()


class DeleteItemVarView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (hasattr(self.request.user, "user_staff")
                and self.request.user.has_perm("in_place.delete_items"))
        
    def post(self, *args, **kwargs):
        form_data = DeleteItemVarForm(self.request.POST)
        if form_data.is_valid():
            public_uuid = form_data.cleaned_data.get("public_uuid")
            ItemVariation.objects.get(public_uuid=public_uuid).delete()
            messages.success(self.request, 
                             "The item-variation was successfully deleted.")
        else:
            messages.error(self.request, 
                           "There was an error during the process. Please try again.")
        return redirect("in_place:menu")
    

delete_itemvar_view = DeleteItemVarView.as_view()


class RenderNewItemView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "in_place/new_item_temp.html"
    context = dict()
    
    def test_func(self):
        return hasattr(self.request.user, "user_staff")
    
    def get(self, *args, **kwargs):
        restaurant = self.request.user.user_staff.restaurant
        revenue_chart, sale_chart = (
            weekly_revenue_chart_data(
                [i//1000 for i in restaurant.weekly_revenue]),
            weekly_sale_chart_data(restaurant.weekly_sale))
        self.context.update({
            "orders": prepare_order_namedtuple(restaurant),
            "sale_chart": sale_chart,
            "revenue_chart": revenue_chart,
        })
        return render(self.request, self.template_name, self.context)


render_new_item_view = RenderNewItemView.as_view()
