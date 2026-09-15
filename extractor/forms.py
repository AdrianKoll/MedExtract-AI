from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .security import login_with_protection


class RateLimitedAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            user, blocked = login_with_protection(self.request, username, password)
            if blocked:
                raise forms.ValidationError('Muitas tentativas. Tente novamente mais tarde.')
            if user is None:
                raise forms.ValidationError('Credenciais inválidas.')
            self.user_cache = user
            self.confirm_login_allowed(user)
        return self.cleaned_data
