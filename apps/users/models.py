from uuid import uuid4
from datetime import datetime

from django.templatetags.static import static
from django.urls import reverse
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, 
                                        BaseUserManager, 
                                        PermissionsMixin)

from phonenumber_field.modelfields import PhoneNumberField

class UserModelManager(BaseUserManager):
    def _create_user(self, 
                     email, 
                     username, 
                     password, 
                     picture, 
                     is_staff, 
                     is_superuser,
                     **extra_fields):
        normalized_email = self.normalize_email(email)
        now = datetime.now()
        user = self.model(
            email=normalized_email,
            username=username,
            picture=picture,
            is_staff=is_staff,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self,
                    email=None,
                    username=None, 
                    password=None, 
                    picture=None, 
                    **extra_fields):
        return self._create_user(email, 
                                 username, 
                                 password, 
                                 picture, 
                                 False, 
                                 False, 
                                 **extra_fields)
    
    def create_superuser(self,
                         username=None,
                         email=None,
                         password=None,
                         picture=None,
                         **extra_fields):
        return self._create_user(email,
                                 username,
                                 password,
                                 picture,
                                 True,
                                 True,
                                 **extra_fields)
    
    def create_staff(self,
                     username=None,
                     email=None,
                     password=None,
                     picture=None,
                     **extra_fields):
        return self._create_user(email,
                                 username,
                                 password, 
                                 picture, 
                                 True,
                                 False,
                                 **extra_fields)
    
    
class UserModel(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, 
                                max_length=50, 
                                db_index=True)
    email = models.EmailField(unique=True, 
                              db_index=True,
                              blank=True,
                              null=True)
    phone_number = PhoneNumberField(region="IR", 
                                    blank=True, 
                                    null=True)
    picture = models.ImageField(upload_to='media/profiles/', 
                                blank=True, 
                                null=True)
    first_name = models.CharField(max_length=50, 
                                  default="not set", 
                                  blank=True)
    last_name = models.CharField(max_length=50, 
                                 default="not set", 
                                 blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    REQUIRED_FIELDS = ["first_name", "last_name"]
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    
    objects = UserModelManager()
    
    class Meta:
        verbose_name_plural = "User Model"
        
    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def user_cart(self):
        return self.user_carts.latest("date_created")
    
    def get_picture_url(self):
        return self.picture.url if self.picture else static(
            "assets/img/no_image_available.png" or None)
    
    def get_dashboard_url(self):
        if hasattr(self, "user_staff"):
            return reverse("in_place:dashboard")
        else:
            return reverse("accounts:profile")
    
    def save(self, *args, **kwargs):
        if not self.email:
            self.email = None
        
        if self.first_name is None:
            self.first_name = "not_set"
        
        if self.last_name is None:
            self.last_name = "not_set"
        super().save(*args, **kwargs)
        