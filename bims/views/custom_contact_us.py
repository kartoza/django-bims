import json
import requests
from contactus.views import ContactUsView
from preferences import preferences


class CustomContactUsView(ContactUsView):
    def _verify_recaptcha(self, token):
        url = 'https://www.google.com/recaptcha/api/siteverify'
        post_data = {
            'secret': preferences.SiteSetting.recaptcha_secret_key,
            'response': token
        }
        response = requests.post(url, data = post_data)
        response_obj = json.loads(response.text)
        if not response_obj['success']:
            return False
        return True

    def form_valid(self, form):
        recaptcha_verified = self._verify_recaptcha(
            self.request.POST.get('recaptcha_token', '')
        )
        if not recaptcha_verified:
            return super(CustomContactUsView, self).form_invalid(form)
        return super(CustomContactUsView, self).form_valid(form)
