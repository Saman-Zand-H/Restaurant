from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    
    def save_user(self, request, user, form, commit=True):
        from allauth.account.utils import user_field
        data = form.cleaned_data
        user_field("picture", data.get("picture"))
        user_field("first_name", data.get("first_name"))
        user_field("last_name", data.get("last_name"))
        return super().save_user(request, user, form, commit)