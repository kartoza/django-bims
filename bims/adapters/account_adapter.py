import re
from django.core.exceptions import ValidationError
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):

    def clean_password(self, password, user=None):
        if re.match(r'^(?=.*?\d)(?=.*?[A-Z])(?=.*?[a-z])[A-Za-z\d]{6,}$',
                    password):
            return password
        else:
            raise ValidationError('Password Error')
