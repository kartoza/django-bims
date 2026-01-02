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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            new_username = '{first_name}_{last_name}'.format(
                first_name=self.data.get('first_name').lower(),
                last_name=self.data.get('last_name').lower()
            )
            if Profile.objects.filter(user__username=new_username).exists():
                counter = 1
                unique_username = new_username
                while Profile.objects.filter(user__username=unique_username).exists():
                    unique_username = f'{new_username}_{counter}'
                    counter += 1
                return unique_username
            return new_username
        return username

    def custom_signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.organization = self.cleaned_data['organization']

        # Generate username from first_name and last_name if not already set
        username = self.cleaned_data.get('username')
        if not username:
            username = '{first_name}_{last_name}'.format(
                first_name=self.cleaned_data['first_name'].lower(),
                last_name=self.cleaned_data['last_name'].lower()
            )
            # Ensure uniqueness
            if Profile.objects.filter(user__username=username).exists():
                counter = 1
                unique_username = username
                while Profile.objects.filter(user__username=unique_username).exists():
                    unique_username = f'{username}_{counter}'
                    counter += 1
                username = unique_username

        user.username = username
        user.save()
        bims_profile, created = Profile.objects.get_or_create(
            user=user
        )
        bims_profile.role = self.cleaned_data['role']
        bims_profile.save()
        return user


