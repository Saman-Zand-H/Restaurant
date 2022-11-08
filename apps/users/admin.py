from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from .models import UserModel


@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    ordering = ["username"]
    sortable_by = ["username", "date_joined", "last_login"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "picture",
                    "about",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = ((
        None,
        {
            "fields": (
                "username",
                "email",
                "first_name",
                "last_name",
                "picture",
                "password1",
                "password2",
                "about",
            ),
            "classes":
            "wide",
        },
    ), )
    list_display = ["name", "username", "email"]
    search_fields = ["name", "username", "email"]
    filter_horizontal = ["groups", "user_permissions"]
    