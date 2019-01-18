from django.conf.urls import url
from sass.views.form import FormView


urlpatterns = [
    url(r'^(?P<site_id>\d+)/$', FormView.as_view(), name='sass-form-page'),
]
