# coding=utf-8

from django.conf.urls import url
from django.urls import path
from rest_framework.documentation import include_docs_urls
from bims.views.map import MapPageView
from bims.views.landing_page import LandingPageView
from bims.api_views.location_site import (
    LocationSiteList,
    LocationSiteDetail,
)
from bims.api_views.location_type import (
    LocationTypeAllowedGeometryDetail
)
from bims.api_views.taxon import TaxonDetail
from bims.api_views.cluster import ClusterList
from bims.api_views.cluster_module import ClusterModuleList
from bims.views.links import LinksCategoryView
from bims.api_views.search import SearchObjects
from bims.views.activate_user import activate_user


api_urls = [
    url(r'^api/location-type/(?P<pk>[0-9]+)/allowed-geometry/$',
        LocationTypeAllowedGeometryDetail.as_view()),
    url(r'^api/location-site/$', LocationSiteList.as_view()),
    url(r'^api/location-site/(?P<pk>[0-9]+)/$',
        LocationSiteDetail.as_view()),
    url(r'^api/taxon/(?P<pk>[0-9]+)/$',
        TaxonDetail.as_view()),
    url(r'^api/cluster/(?P<administrative_level>\w+)/$',
        ClusterList.as_view()),
    url(r'^api/cluster-module/$',
        ClusterModuleList.as_view()),
    url(r'^api/search/(?P<query_value>\w+)/$',
        SearchObjects.as_view(), name='search-api'),
]

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing-page'),
    path('map', MapPageView.as_view()),
    url(r'^links/', LinksCategoryView.as_view(), name = 'link_list'),
    url(r'^api/docs/', include_docs_urls(title='BIMS API')),
    url(r'^activate-user/(?P<username>[\w-]+)/$',
        activate_user, name='activate-user')
] + api_urls
