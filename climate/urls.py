from django.urls import path, re_path

from climate.views import ClimateSiteView, ClimateUploadView

app_name = 'climate'

urlpatterns = [
    path('upload/', ClimateUploadView.as_view(), name='climate-upload'),
    re_path(r'^(?P<site_id>\d+)/$',
            ClimateSiteView.as_view(),
            name='climate-site'),
    re_path(r'^(?P<site_id>\d+)/(?P<year>\d{4})/$',
            ClimateSiteView.as_view(),
            name='climate-site'),
]
