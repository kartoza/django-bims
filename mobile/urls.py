from django.conf.urls import url

from mobile.api_views.location_site import NearestLocationSites


urlpatterns = [
    url(r'^nearest-sites/$',
        NearestLocationSites.as_view(),
        name='mobile-nearest-sites'
        ),
]
