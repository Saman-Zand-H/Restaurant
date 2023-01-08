from allauth.account.adapter import DefaultAccountAdapter
from phonenumber_field.phonenumber import PhoneNumber


class AccountAdapter(DefaultAccountAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages["username_taken"] = ("This username has already "
                                                 "been taken. Try another one")
    
    def save_user(self, request, user, form, commit=True):
        from allauth.account.utils import user_field
        data = form.cleaned_data
        user_field(user, "picture", data.get("picture"))
        user_field(user, "first_name", data.get("first_name"))
        user_field(user, "last_name", data.get("last_name"))
        phone_number = data.get("phone_number")
        if phone_number is not None and isinstance(phone_number, PhoneNumber):
            print(phone_number)
            user_field(user, "phone_number", data.get("phone_number").as_e164)
        return super().save_user(request, user, form, commit)
    