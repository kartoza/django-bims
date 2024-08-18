from django import forms
from preferences.admin import PreferencesAdmin

from bims.models.site_setting import SiteSetting

SECRET_INPUTS = [
    'recaptcha_secret_key',
    'iucn_api_key',
    'cites_token_api',
    'virtual_museum_token',
    'resend_api_key',
    'github_feedback_token'
]


class SiteSettingAdminForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = '__all__'

    recaptcha_secret_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    iucn_api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    cites_token_api = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    virtual_museum_token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    resend_api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    github_feedback_token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    minisass_token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(SiteSettingAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            for secret_input in SECRET_INPUTS:
                self.fields[secret_input].widget.attrs['placeholder'] = '******'
                self.fields[secret_input].required = False


class SiteSettingAdmin(PreferencesAdmin):
    form = SiteSettingAdminForm

    def save_model(self, request, obj, form, change):
        if change:
            for secret_input in SECRET_INPUTS:
                if secret_input in form.changed_data:
                    setattr(obj, secret_input, form.cleaned_data[secret_input])
                else:
                    current_value = getattr(obj, secret_input)
                    setattr(obj, secret_input, current_value)
        obj.save()

