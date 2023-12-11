from django.urls import re_path, path

from mobile.api_views.abiotic_list import AbioticList
from mobile.api_views.add_sass import AddSASS
from mobile.api_views.choices import AllChoicesApi
from mobile.api_views.location_site import NearestLocationSites
from mobile.api_views.obtain_auth_token import CustomObtainAuthToken
from mobile.api_views.sass_taxa import SassTaxaListApi
from mobile.api_views.taxa import AllTaxa
from mobile.api_views.add_site_visit import AddSiteVisit
from mobile.api_views.add_location_site import AddLocationSiteView
from mobile.api_views.taxon_group import TaxonGroupList
from mobile.api_views.source_reference import SourceReferenceMobileList
from mobile.api_views.river import FetchRiverName
from mobile.api_views.wetland import FetchWetland


urlpatterns = [
    re_path(r'^add-location-site/$',
        AddLocationSiteView.as_view(),
        name='mobile-add-location-site'),
    re_path(r'^add-site-visit/$',
        AddSiteVisit.as_view(),
        name='mobile-add-site-visit'),
    re_path(r'^all-taxa/$',
        AllTaxa.as_view(),
        name='all-taxa'),
    re_path(r'^api-token-auth/',
        CustomObtainAuthToken.as_view(),
        name='api_token_auth'),
    re_path(r'^choices/',
        AllChoicesApi.as_view(),
        name='all-choices'),
    re_path(r'^nearest-sites/$',
        NearestLocationSites.as_view(),
        name='mobile-nearest-sites'),
    re_path(r'^taxon-group/$',
        TaxonGroupList.as_view(),
        name='taxon-group-list'),
    re_path(r'^source-references/$',
        SourceReferenceMobileList.as_view(),
        name='source-reference-mobile-list'),
    re_path(r'^sass-taxa-list/$',
        SassTaxaListApi.as_view(),
        name='sass-taxa-list'),
    re_path(r'^add-sass/$',
        AddSASS.as_view(),
        name='mobile-add-sass'),
    re_path(r'^abiotic-list/$',
        AbioticList.as_view(),
        name='abiotic-list'),
    path('river/',
        FetchRiverName.as_view(),
        name='fetch-river-name'),
    path('wetland/',
         FetchWetland.as_view(),
         name='fetch-wetland'),
]
