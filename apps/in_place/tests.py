from django.test import TransactionTestCase, LiveServerTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from seleniumlogin import force_login
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import shlex
import random
import subprocess
from time import sleep
from functools import partial
from datetime import time
from string import ascii_letters

from restaurants.models import (Restaurant, 
                                RestaurantType, 
                                Item, 
                                ItemVariation, 
                                Cuisine)
from in_place.models import Staff
from in_place.forms import CreateStaffForm


def random_str():
    return "".join(random.choices(ascii_letters, k=8))


class TestViews(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create(
            username="test",
            first_name=random_str(),
            last_name=random_str(),
            password="test123456")
        res_type = RestaurantType.objects.create(name="test_type")
        cls.restaurant = Restaurant.objects.create(name=random_str(),
                                                   opens_at=time(10),
                                                   closes_at=time(22),
                                                   restaurant_type=res_type,
                                                   table_count=random.randint(1, 50))
        cls.staff = Staff.objects.create(user=cls.user,
                                         role="m",
                                         restaurant=cls.restaurant,
                                         income=0)
        cuisine = Cuisine.objects.create(name="pizzas", restaurant=cls.restaurant)
        item = Item.objects.create(name="pepperoni", cuisine=cuisine)
        ItemVariation.objects.create(name="mini", price=25000, item=item)
    
    def test_staff_creation_success(self):
        self.client.force_login(self.user)
        url = reverse("in_place:staff")  
        users_init_count = get_user_model().objects.count()   
        staff_init_count = Staff.objects.count() 
        data = {
            "username": "testusername",
            "first_name": "testfirstname",
            "last_name": "testlastname",
            "phone_number": "+989991119911",
            "password1": "test123456",
            "password2": "test123456",
            "email": "bullshit@bullshit.gov",
            "role": "m",
            "income": 250000,
        }          
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(get_user_model().objects.count(), users_init_count+1)
        self.assertEqual(Staff.objects.count(), staff_init_count+1)
        msgs = [*get_messages(resp.wsgi_request)]
        self.assertEqual(str(msgs[-1]), "User was successfully created.")
        expected = ["testusername", 
                    "testfirstname", 
                    "testlastname", 
                    "+989991119911", 
                    "bullshit@bullshit.gov", 
                    "m", 
                    250000]
        user = get_user_model().objects.last()
        user_staff = Staff.objects.last()
        values = [user.username,
                  user.first_name,
                  user.last_name,
                  user.phone_number,
                  user.email,
                  user_staff.role,
                  user_staff.income]
        self.assertEqual(values, expected)
        
    def test_staff_creation_failed(self):
        self.client.force_login(self.user)
        url = reverse("in_place:staff")
        users_init_count = get_user_model().objects.count()
        staff_init_count = Staff.objects.count()
        data = {
            "username": "testusername",
            "first_name": "testfirstname",
            "last_name": "testlastname",
            "phone_number": "asdfasdf",
            "password1": "test123456",
            "password2": "test123456",
            "email": "just bullshit",
            "role": "bob",
            "income": "Free lunch",
        }     
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(response=resp,
                             form="new_form",
                             field="phone_number", 
                             errors="Enter a valid phone number (e.g. +12125552368).")
        msgs = [*get_messages(resp.wsgi_request)]
        self.assertFormError(response=resp,
                             form="new_form",
                             field="email",
                             errors="Enter a valid email address.")
        self.assertFormError(response=resp,
                             form="new_form",
                             field="role",
                             errors=("Select a valid choice. "
                                     "bob is not one of the available choices."))
        self.assertFormError(response=resp,
                             form="new_form",
                             field="income",
                             errors="Enter a whole number.")
        self.assertEqual(staff_init_count, Staff.objects.count())
        self.assertEqual(users_init_count, get_user_model().objects.count())
        self.assertEqual(str(msgs[-1]), 
                         "Invalid input detected. Please try again more carefully.")


class TestUI(StaticLiveServerTestCase):
    fixtures = ["users.json", "in_place.json", "restaurants.json"]
    
    @classmethod
    def _set_browser_options(cls):
        chrome_options = webdriver.chrome.options.Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_prefs = dict()
        chrome_options.experimental_options["prefs"] = chrome_prefs
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        return chrome_options
    
    @classmethod
    def _driver_path(cls):
        # There are internet connection problems with downloading 
        # the webdriver from inside the container, so we download it inside 
        # the dockerfile, which causes it to cache the downloaded file, then we'll
        # access the cached file.
        return subprocess.check_output(
            shlex.split("find /root/.wdm/drivers/chromedriver/linux64 "
                        "-name chromedriver")).decode().replace("\n", "")
    
    @classmethod
    def _create_driver(cls, store_logs=False):
        d = DesiredCapabilities.CHROME
        if store_logs:
            d["goog:loggingPrefs"] = {'browser': 'ALL'}
        return webdriver.Chrome(
            executable_path=cls._driver_path(),
            options=cls._set_browser_options(),
            desired_capabilities=d
        )
        
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.driver = cls._create_driver()
            cls.wait = WebDriverWait(cls.driver, 5)
            cls.url = cls.live_server_url
        except:
            cls.tearDownClass()
            raise
        
    def user_login(self, user_id=1):
        user = get_user_model().objects.filter(id=user_id)
        if user.exists():
            force_login(user.first(), 
                        self.driver, 
                        self.url)
            return user
        print("[!] User couldn't be found. Exiting...")
        self.driver.close()
        self.tearDownClass()
        
    def _fill_input(self, element_id:str, input_value:str):
        elem = self.driver.find_element("id", element_id)
        elem.click()
        elem.send_keys(input_value)
        
    def test_create_staff(self):
        url = self.url + reverse("in_place:staff")
        self.user_login()
        staff_initial_count = Staff.objects.count()
        self.driver.get(url)
        sleep(.5)
        # Selenium recognizes this element as blocked and won't click 
        # on it, so we just use js to accomplish this task
        self.driver.execute_script(
            "arguments[0].click();", 
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "createStaffBtn"))))
        self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "createStaff")))
        self._fill_input("username", "test_username")
        self._fill_input("id_email", "bullshit@bullshit.gov")
        self._fill_input("id_first_name", "first name")
        self._fill_input("id_last_name", "last name")
        self._fill_input("password1", "test123456")
        self._fill_input("password2", "test123456")
        self._fill_input("new_income", 250000)
        self.driver.execute_script(
            "arguments[0].click();", 
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@id='role_m']"))))
        self.driver.execute_script(
            "arguments[0].click();", 
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "new_staff_btn"))))
        sleep(1)
        
        self.assertEqual(Staff.objects.count(), staff_initial_count+1)
        new_staff = Staff.objects.latest("date_created")
        new_user = get_user_model().objects.latest("date_joined")
        self.assertEqual(new_user.username, "test_username")
        self.assertEqual(new_staff.role, "m")
        
    def _messages_appears(self, msg, tag):
        # TODO: complete this func
        pass
        