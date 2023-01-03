from genericpath import exists
from django.shortcuts import render, redirect, reverse
from django.db.models import Max, Min, F, Avg
from django.http.response import (HttpResponse, 
                                  JsonResponse, 
                                  HttpResponseBadRequest)
from django.views import View
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from uuid import UUID
from functools import partial
from logging import getLogger
from asgiref.sync import sync_to_async

from delivery.models import DeliveryCart
from .models import Restaurant, Cuisine, Item, RestaurantType, Review
from .forms import FilterItems, FilterRestaurants
from .utils import paginate
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
            
            await sync_to_async(self.context.update)({
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
    
    async def get(self, *args, **kwargs):
        restaurant = await Restaurant.objects.aget(
            public_uuid=kwargs.get("public_uuid"))
        reviews = await sync_to_async(Review.objects.filter)(
                item__cuisine__restaurant=restaurant)
        self.context.update({
            "restaurant": restaurant,
            "reviews": reviews,
        })
        return await sync_to_async(render)(self.request, 
                                           self.template_name, 
                                           self.context)


restaurant_page_view = RestaurantPageView.as_view()
