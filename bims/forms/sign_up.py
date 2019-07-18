from allauth.account.forms import SignupForm
from django import forms
from bims.models import Profile


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=150,
        label='First Name',
        required=True)
    last_name = forms.CharField(
        max_length=150,
        label='Last Name',
        required=True
    )
    organization = forms.CharField(
        max_length=100,
        label='Organization/Institution',
        required=True
    )
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        initial='citizen',
        required=True
    )

    def custom_signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.organization = self.cleaned_data['organization']
        user.save()
        bims_profile, created = Profile.objects.get_or_create(
            user=user
        )
        bims_profile.role = self.cleaned_data['role']
        bims_profile.save()
        return user
