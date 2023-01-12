from django.shortcuts import render, redirect, reverse
from django.db.models import F
from django.db import transaction
from django.http.response import (JsonResponse, 
                                  HttpResponseBadRequest)
from django.template.loader import get_template
from django.views import View
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from allauth.account.views import SignupView
from allauth.account import app_settings
from allauth.account.utils import complete_signup
from allauth.exceptions import ImmediateHttpResponse

from logging import getLogger
from asgiref.sync import sync_to_async

from .models import Restaurant, RestaurantType, Review
from .forms import FilterItems, FilterRestaurants, NewPartnerForm
from .utils import paginate
from in_place.models import Staff
from users.forms import SignupForm
from search_index.es_queries import RestaurantQuery
from search_index.documents import RestaurantDocument


logger = getLogger(__name__)


class HomePageView(View):
    template_name = "restaurants/home.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        return render(self.request, self.template_name, self.context)


home_page_view = HomePageView.as_view()


class ListRestaurantsView(View):
    template_name = "restaurants/list_restaurants.html"
    context = dict()
    
    async def get(self, *args, **kwargs):
        form_data = FilterRestaurants(self.request.GET)
        if form_data.is_valid():
            lat = float(form_data.cleaned_data.get("lat") or 0.0)
            lon = float(form_data.cleaned_data.get("lon") or 0.0)
            page = form_data.cleaned_data.get("page", 1)
            types = RestaurantType.objects.all()
            restaurant_type = form_data.cleaned_data.get("type")
            
            if lat and lon:
                point = Point(lon, lat, srid=4326)                
                values = await sync_to_async(Restaurant.objects.alias)(
                    loc=F("info__geo_address"))
                values = await sync_to_async(values.alias)(
                    loc_distance=Distance(point, "loc"))
                values = values.order_by("-loc_distance")
            else:
                values = await sync_to_async(Restaurant.objects.all().order_by)("score")
            
            if restaurant_type:
                types_q = await sync_to_async(RestaurantType.objects.filter)(
                    name=restaurant_type)
                if await sync_to_async(types_q.exists)():
                    restaurant_type = await types_q.afirst()
                    values = await sync_to_async(values.filter)(
                        restaurant_type=restaurant_type)
                    
            paginated_data = await sync_to_async(paginate)(page, values, 6)
            
            self.context.update({
                "page": paginated_data[0],
                "paginator": paginated_data[1],
                "types": types,
                "filter_form": FilterRestaurants()
            })
            
            response = await sync_to_async(render)(request=self.request,
                                                   template_name=self.template_name,
                                                   context=self.context)
            
            await sync_to_async(response.set_cookie)("lat", lat)
            await sync_to_async(response.set_cookie)("lon", lon)
        else:
            await sync_to_async(messages.warning)(self.request, 
                                                  "Invalid parameters were provided. Request aborted.")
        return response
        
        
list_restaurants_view = ListRestaurantsView.as_view()


class SearchRestaurantsView(View):
    def get(self, *args, **kwargs):
        form_data = FilterRestaurants(self.request.GET)
        if form_data.is_valid():
            get_data = form_data.cleaned_data
            match get_data.get("op_type"):
                case "search":
                    self.request.session["has_free_delivery"] = get_data.get(
                        "has_free_delivery")
                    self.request.session["is_open"] = get_data.get("is_open")
                    self.request.session["name"] = get_data.get("name")
                    self.request.session["score"] = get_data.get("score")
                case "pag":
                    get_data = {
                        "has_free_delivery": self.request.session.get(
                            "has_free_delivery"),
                        "is_open": self.request.session.get("is_open"),
                        "name": self.request.session.get("name"),
                        "score": self.request.session.get("score"),
                    }
                case _:
                    return HttpResponseBadRequest()
            query = RestaurantQuery(get_data).query
            doc = RestaurantDocument.search().query(
                query).execute().to_dict()["hits"]["hits"]
            paginated_data = paginate(self.request.GET.get("page", 1), doc, 6)
            results = {"hits": paginated_data[0].object_list,
                       "page": {
                           "has_next_page": paginated_data[0].has_next(),
                           "has_previous_page": paginated_data[0].has_previous(),
                           "next_page_number": (paginated_data[0].next_page_number() 
                                                if paginated_data[0].has_next() else False),
                           "previous_page_number": (paginated_data[0].previous_page_number() 
                                                    if paginated_data[0].has_previous() else False),
                           "page": paginated_data[0].number,
                           "object_list": paginated_data[0].object_list,
                           "num_pages": paginated_data[1].num_pages},
                       }
            return JsonResponse(results)
        return HttpResponseBadRequest()
    

search_restaurants_view = SearchRestaurantsView.as_view()


class RestaurantPageView(View):
    template_name = "restaurants/restaurant.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        restaurant = Restaurant.objects.get(
            public_uuid=kwargs.get("public_uuid"))
        reviews = Review.objects.filter(
                item__cuisine__restaurant=restaurant)
        self.context.update({
            "restaurant": restaurant,
            "reviews": reviews,
        })
        return render(self.request, 
                      self.template_name, 
                      self.context)


restaurant_page_view = RestaurantPageView.as_view()



# todo: this has to become csrf exempt.
class NewPartnerAjax(SignupView):
    form_template_name = "restaurants/new_partner_form.html"
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        print("at form.")
        # By assigning the User to a property on the view, we allow subclasses
        # of SignupView to access the newly created User instance
        self.user = form.save(self.request)
        try:
            print("position one.")
            template = get_template(self.form_template_name)
            complete_signup(
                self.request,
                self.user,
                app_settings.EMAIL_VERIFICATION,
                self.get_success_url(),
            )
            data = {"status_code": 200,
                    "template": str(template.render({"form": NewPartnerForm()}))}
        except ImmediateHttpResponse:
            data = {"status_code": 403}
        return JsonResponse(data)
    
    
new_partner_ajax = NewPartnerAjax.as_view()
        


class NewPartnerView(View):
    template_name = "restaurants/new_partner.html"
    context = dict()
    
    def get(self, *args, **kwargs):
        if (self.request.user.is_authenticated
            and not hasattr(self.request.user, "user_staff")):
            self.context.update({"form": NewPartnerForm()})
        else:
            self.context.update({
                "form": SignupForm()
            })
        return render(self.request, self.template_name, self.context)
    
    def post(self, *args, **kwargs):
        form = NewPartnerForm(self.request.POST)
        if (form.is_valid() 
            and self.request.user.is_authenticated
            and not hasattr(self.request.user, "user_staff")):
            role = form.cleaned_data.pop("role")
            with transaction.atomic():
                try:
                    restaurant = Restaurant.objects.create(**form.cleaned_data)
                    Staff.objects.create(
                        user=self.request.user,
                        restaurant=restaurant,
                        role=role,
                        income=0
                    )
                except Exception as e: 
                    logger.debug("[!] Exception occurred: ", e)
                    self.context.update({"form": form})
                    return render(self.request, self.template_name, self.context)
            messages.success(self.request, "Congratualations! You're now one of our partners.")
            return redirect("in_place:dashboard")
        self.context.update({"form": form})
        return render(self.request, self.template_name, self.context)


new_partner_view = NewPartnerView.as_view()
