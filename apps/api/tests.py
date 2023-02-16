from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from django.utils import timezone
from datetime import datetime, time
from http.cookies import SimpleCookie
import json
import string
import random


def random_str(length=10):
        return "".join(random.choices(string.ascii_letters, k=length))


def generate_user(username,
                  password,
                  is_superuser=False):
        return get_user_model().objects.create(
            username=username,
            is_superuser=bool(is_superuser),
            password=password,
            first_name=random_str(),
            last_name=random_str()
        )


class AuthTest(APITestCase):
    fixtures = ["api_users.json"]
    
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username="api_test")
        self._get_token()
        self.client.force_login(self.user)
        
    def _get_token(self,
                  username="api_test",
                  password="13840000"):
        data = {
            "username": username,
            "password": password
        }
        url = reverse("api_v1:token_obtain_pair")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        tokens = json.loads(response.content.decode())
        self.access, self.refresh = tokens["access"], tokens["refresh"]
    
    def test_jwt_token_header(self):
        self.client.logout()
        
        url = reverse("rest_user_details")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(url,
                                   HTTP_AUTHORIZATION=f"Bearer {self.access}")
        self.assertNotEqual(response.status_code, 403)
        self.assertEqual(response.status_code, 200)
        

    def test_jwt_token_cookie(self):
        self.client.logout()
        
        url = reverse("rest_user_details")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        self.client.cookies = SimpleCookie({
            settings.JWT_AUTH_COOKIE: self.access,
            settings.JWT_AUTH_REFRESH_COOKIE: self.refresh
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        


class RestaurantsTest(TestCase):
    fixtures = ["api_restaurants.json", "api_iranian_cities.json"]

    def setUp(self):
        super().setUp()
        self.user = generate_user("api_test", "test123456", 1)
        self.client.force_login(self.user)
    
    def test_check_permission(self):
        self.client.logout()
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 403)
        
        self.client.force_login(self.user)
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        
    def test_create_restaurant(self):
        url = reverse("api_v1:restaurants-list")
        
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        
        data = {
            "name": "this is a test",
            "opens_at": time(1).isoformat(),
            "closes_at": time(16).isoformat(),
            "restaurant_type_id": 1
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
    
    def test_create_restaurant_failure(self):
        url = reverse("api_v1:restaurants-list")
        data = {
            "user": self.user.pk,
            "name": "this is a test",
            "table_count": 0,
            "opens_at": time(1).isoformat(),
            "closes_at": time(16).isoformat(),
            "restaurant_type_id": 9 # invalid record
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
    
    def test_create_restaurant_location(self):
        url = reverse("api_v1:restaurant_location-list")
        self.assertEqual(self.client.get(url).status_code, 200)
        data = {
            "geo_address": "POINT(0 0)",
            "address": "This is a test address",
            "city_id": random.randint(1, 50),
            "province_id": random.randint(1, 20)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        
    def test_create_restaurant_location_failure(self):
        url = reverse("api_v1:restaurant_location-list")
        data = {
            "geo_address": {
                "type": "Point",
                "coordinates": [-500, -500] # Invalid
            },
            "address": "", # invalid
            "city_id": "",
            "province_id": ""
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        
    def test_create_cuisine(self):
        url = reverse("api_v1:cuisine-list")
        self.assertEqual(self.client.get(url).status_code, 200)
        
        data = {
            "restaurant_public_uuid": "6d99e928-5bb6-4751-9048-842214427bca",
            "name": "Test Cuisine"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
    
    def test_create_cuisine_failure(self):
        url = reverse("api_v1:cuisine-list")
        data = {
            "name": "Test Cuisine"
            # Invalid: Missed Restaurant
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        
    def test_create_item(self):
        url = reverse("api_v1:item-list")
        self.assertEqual(self.client.get(url).status_code, 200)
        
        data  = {
            "cuisine_public_uuid": "58c0a1e1-b4e6-467e-827b-c3fd8e3ad704",
            "name": "test item"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        
    def test_create_item_failure(self):
        url = reverse("api_v1:item-list")
        data = {
            "name": "invalid - no cuisine"
            # invalid: missed cuisine
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        
    def test_create_itemvar(self):
        url = reverse("api_v1:item_var-list")
        self.assertEqual(self.client.get(url).status_code, 200)
        
        data = {
            "item_public_uuid": "1c9cfe55-3a26-47a3-9e60-548aa64b7a95",
            "name": "is this working dude?",
            "price": 25e5
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
    
    def test_create_itemvar_failure(self):
        url = reverse("api_v1:item_var-list")
        data = {
            "name": "nope dude, not today",
            "price": -2 # invalid
            # invalid: missed item
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        
    def test_get_types(self):
        url = reverse("api_v1:restaurant_types-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_create_review(self):
        url = reverse("api_v1:review-list")
        self.assertEqual(self.client.get(url).status_code, 200)
        
        data = {
            "item_public_uuid": "1c9cfe55-3a26-47a3-9e60-548aa64b7a95",
            "user_id": self.user.pk,
            "review": "It was aweful. Leave this job buddy!",
            "score": 1
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        
    def test_create_review_failure(self):
        url = reverse("api_v1:review-list")
        data = {
            "item_public_uuid": "1c9cfe55-3a26-47a3-9e60-548aa64b7a95",
            "review": "bluh bluh bluh",
            "score": -1 # invalid
            # invalid: missed user
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        
