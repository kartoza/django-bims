from django.views.generic import DetailView
from django.contrib.auth import get_user_model


class ProfileView(DetailView):
    template_name = 'user/profile.html'
    model = get_user_model()
    slug_field = 'username'
