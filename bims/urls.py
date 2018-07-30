# coding=utf-8

from django.contrib.auth.decorators import login_required
from django.conf.urls import url, include
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

from rest_framework.documentation import include_docs_urls
from bims.views.map import MapPageView
from bims.views.landing_page import LandingPageView
from bims.api_views.location_site import (
    LocationSiteList,
    LocationSiteDetail,
    LocationSiteClusterList
)
from bims.api_views.location_type import (
    LocationTypeAllowedGeometryDetail
)
from bims.api_views.non_biodiversity_layer import (
    NonBiodiversityLayerList
)
from bims.api_views.taxon import TaxonDetail
from bims.api_views.cluster import ClusterList
from bims.api_views.cluster_collection import (
    ClusterCollection,
    ClusterCollectionExtent
)
from bims.api_views.cluster_collection_by_taxon import (
    ClusterCollectionByTaxon,
    ClusterCollectionByTaxonExtent
)
from bims.api_views.collector import CollectorList
from bims.api_views.category_filter import CategoryList
from bims.views.bibliography import (
    EntryListView,
    EntryBatchImportView,
)
from bims.api_views.search import SearchObjects
from bims.api_views.validate_object import ValidateObject
from bims.api_views.get_biorecord import GetBioRecords
from bims.views.links import LinksCategoryView
from bims.views.activate_user import activate_user
from bims.views.csv_upload import CsvUploadView
from bims.views.shapefile_upload import ShapefileUploadView, process_shapefiles
from bims.views.under_development import UnderDevelopmentView
from bims.views.non_validated_list import NonValidatedObjectsView

api_urls = [
    url(r'^api/location-type/(?P<pk>[0-9]+)/allowed-geometry/$',
        LocationTypeAllowedGeometryDetail.as_view()),
    url(r'^api/location-site/cluster/$', LocationSiteClusterList.as_view()),
    url(r'^api/location-site/$', LocationSiteList.as_view()),
    url(r'^api/location-site/(?P<pk>[0-9]+)/$',
        LocationSiteDetail.as_view()),
    url(r'^api/taxon/(?P<pk>[0-9]+)/$',
        TaxonDetail.as_view()),
    url(r'^api/cluster/(?P<administrative_level>\w+)/$',
        ClusterList.as_view()),
    url(r'^api/cluster/collection/records/extent/$',
        ClusterCollectionExtent.as_view()),
    url(r'^api/cluster/collection/records/$',
        ClusterCollection.as_view()),
    url(r'^api/cluster/collection/taxon/(?P<pk>[0-9]+)/extent/$',
        ClusterCollectionByTaxonExtent.as_view()),
    url(r'^api/cluster/collection/taxon/(?P<pk>[0-9]+)/$',
        ClusterCollectionByTaxon.as_view()),
    url(r'^api/search/$',
        SearchObjects.as_view(), name='search-api'),
    url(r'^api/list-collector/$',
        CollectorList.as_view(), name='list-collector'),
    url(r'^api/list-category/$',
        CategoryList.as_view(), name='list-date-category'),
    url(r'^api/list-non-biodiversity/$',
        NonBiodiversityLayerList.as_view(),
        name='list-non-biodiversity-layer'),
    url(r'^api/validate-object/$',
        ValidateObject.as_view(), name='validate-object'),
    url(r'^api/get-bio-object/$',
        GetBioRecords.as_view(), name='get-bio-object'),
]

bibliography_urls = [
    url('^$', EntryListView.as_view(), name='entry_list'),
    url('^import/$', EntryBatchImportView.as_view(), name='import'),
]

urlpatterns = [
    url(r'^$', LandingPageView.as_view(), name='landing-page'),
    url(r'^map/$', MapPageView.as_view()),
    url(r'^profile/$',
        login_required(lambda request: RedirectView.as_view(
            url=reverse_lazy('profile_detail', kwargs={
                'username': request.user.username
            }), permanent=False)(request)), name='user-profile'),
    url(r'^upload/$', login_required(CsvUploadView.as_view()),
        name='csv-upload'),
    url(r'^upload_shp/$', login_required(ShapefileUploadView.as_view()),
        name='shapefile-upload'),
    url(r'^process_shapefiles/$', process_shapefiles,
        name='process_shapefiles'),
    url(r'^links/$', LinksCategoryView.as_view(), name = 'link_list'),
    url(r'^bibliography/',
        include((bibliography_urls, 'bims'), namespace = 'td_biblio')),

    url(r'^api/docs/', include_docs_urls(title='BIMS API')),
    url(r'^activate-user/(?P<username>[\w-]+)/$',
        activate_user, name='activate-user'),
    url(r'^under-development/$',
        UnderDevelopmentView.as_view(), name='under-development'),
    url(r'^nonvalidated-list/$',
        NonValidatedObjectsView.as_view(), name='nonvalidated-list'),
] + api_urls
