from allauth.account.forms import SignupForm
from django import forms
from bims.models import Profile
from bims.models.profile import Role


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
    role = forms.ModelChoiceField(
        queryset=Role.objects.all().order_by('order'),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        try:
            first_role = Role.objects.all().order_by('order').first()
            if first_role:
                self.fields['role'].initial = first_role
        except Role.DoesNotExist:
            pass
        # For django-allauth 65.x: properly configure username field
        if 'username' in self.fields:
            self.fields['username'].required = False
            self.fields['username'].widget = forms.HiddenInput()

    def clean(self):
        """Override clean to generate username before form validation completes."""
        cleaned_data = super().clean()

        # Generate username from first_name and last_name if not provided
        if not cleaned_data.get('username'):
            first_name = cleaned_data.get('first_name', '').lower()
            last_name = cleaned_data.get('last_name', '').lower()

            if first_name and last_name:
                base_username = f'{first_name}_{last_name}'
                username = base_username

                # Ensure uniqueness
                from django.contrib.auth import get_user_model
                User = get_user_model()
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}_{counter}'
                    counter += 1

                cleaned_data['username'] = username

        return cleaned_data

    def custom_signup(self, request, user):
        """Called after the user is created to set additional fields."""
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.organization = self.cleaned_data['organization']
        # Username is already set from clean() method
        user.save()

        # Create or get the BIMS profile
        bims_profile, created = Profile.objects.get_or_create(user=user)
        bims_profile.role = self.cleaned_data['role']
        bims_profile.save()

        return user


