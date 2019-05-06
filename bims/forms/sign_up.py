from allauth.account.forms import SignupForm
from django import forms


class CustomSignupForm(SignupForm):
    full_name = forms.CharField(
        max_length=150,
        label='Full Name',
        required=True)
    organization = forms.CharField(
        max_length=100,
        label='Organization',
        required=True
    )

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user
