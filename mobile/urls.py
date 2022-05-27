from django.conf.urls import url

from rest_framework.authtoken.views import obtain_auth_token

from mobile.api_views.choices import AllChoicesApi
from mobile.api_views.location_site import NearestLocationSites
from mobile.api_views.taxa import AllTaxa


urlpatterns = [
    url(r'^api-token-auth/', obtain_auth_token, name='api_token_auth'),
    url(r'^nearest-sites/$',
        NearestLocationSites.as_view(),
        name='mobile-nearest-sites'
        ),
    url(r'^choices/', AllChoicesApi.as_view(), name='all-choices'),
    url(r'^all-taxa/$',
        AllTaxa.as_view(),
        name='all-taxa'
        ),
]
