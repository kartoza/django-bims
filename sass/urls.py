from django.conf.urls import url
from sass.views.form import FormView


urlpatterns = [
    url(r'^$', FormView.as_view(), name='sass-form-page'),
]
