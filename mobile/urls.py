from django.conf.urls import url

from rest_framework.authtoken.views import obtain_auth_token

from mobile.api_views.location_site import NearestLocationSites


urlpatterns = [
    url(r'^api-token-auth/', obtain_auth_token, name='api_token_auth'),
    url(r'^nearest-sites/$',
        NearestLocationSites.as_view(),
        name='mobile-nearest-sites'
        ),
]
