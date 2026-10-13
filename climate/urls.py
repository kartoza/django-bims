from django.urls import path, re_path

from climate.views import (
    ClimateSiteView,
    ClimateStationDescriptionView,
    ClimateUploadView,
    ClimateDashboardMultipleSitesView,
    ClimateDashboardMultipleSitesApiView,
)

app_name = 'climate'

urlpatterns = [
    path('upload/', ClimateUploadView.as_view(), name='climate-upload'),
    path(
        'dashboard-multi-sites/',
        ClimateDashboardMultipleSitesView.as_view(),
        name='climate-dashboard-multi-sites',
    ),
    path(
        'dashboard-multi-sites-api/',
        ClimateDashboardMultipleSitesApiView.as_view(),
        name='climate-dashboard-multi-sites-api',
    ),
    re_path(r'^(?P<site_id>\d+)/description/$',
            ClimateStationDescriptionView.as_view(),
            name='climate-station-description'),
    re_path(r'^(?P<site_id>\d+)/$',
            ClimateSiteView.as_view(),
            name='climate-site'),
    re_path(r'^(?P<site_id>\d+)/(?P<year>\d{4})/$',
            ClimateSiteView.as_view(),
            name='climate-site'),
]
