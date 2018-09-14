import re
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from geonode.people.adapters import LocalAccountAdapter


class AccountAdapter(LocalAccountAdapter):

    def get_login_redirect_url(self, request):
        map_path = reverse('map-page')
        return map_path

    def clean_password(self, password, user=None):
        if re.match(r'^(?=.*?\d)(?=.*?[A-Z])(?=.*?[a-z])[A-Za-z\d]{6,}$',
                    password):
            return password
        else:
            raise ValidationError('Password Error')
