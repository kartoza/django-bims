from django.conf.urls import url

from rest_framework.authtoken.views import obtain_auth_token

from mobile.api_views.choices import AllChoicesApi
from mobile.api_views.location_site import NearestLocationSites
from mobile.api_views.taxa import AllTaxa
from mobile.api_views.add_site_visit import AddSiteVisit
from mobile.api_views.add_location_site import AddLocationSiteView
from mobile.api_views.taxon_group import TaxonGroupList
from mobile.api_views.source_reference import SourceReferenceMobileList


urlpatterns = [
    url(r'^add-location-site/$',
        AddLocationSiteView.as_view(),
        name='mobile-add-location-site'),
    url(r'^add-site-visit/$',
        AddSiteVisit.as_view(),
        name='mobile-add-site-visit'),
    url(r'^all-taxa/$',
        AllTaxa.as_view(),
        name='all-taxa'),
    url(r'^api-token-auth/',
        obtain_auth_token,
        name='api_token_auth'),
    url(r'^choices/',
        AllChoicesApi.as_view(),
        name='all-choices'),
    url(r'^nearest-sites/$',
        NearestLocationSites.as_view(),
        name='mobile-nearest-sites'),
    url(r'^taxon-group/$',
        TaxonGroupList.as_view(),
        name='taxon-group-list'),
    url(r'^source-references/$',
        SourceReferenceMobileList.as_view(),
        name='source-reference-mobile-list')
]
