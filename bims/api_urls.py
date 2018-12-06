from django.conf.urls import url
from rest_framework.documentation import include_docs_urls
from bims.api_views.boundary import (
    BoundaryList,
    BoundaryGeojson
)
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
from bims.api_views.taxon import (
    TaxonDetail,
    TaxonSimpleList,
    TaxonForDocument,
)
from bims.api_views.cluster import ClusterList
from bims.api_views.collection import (
    GetCollectionExtent,
    CollectionDownloader,
    ClusterCollection
)
from bims.api_views.collector import CollectorList
from bims.api_views.reference_category import ReferenceCategoryList
from bims.api_views.category_filter import CategoryList
from bims.api_views.reference_list import ReferenceList, ReferenceEntryList
from bims.api_views.search import SearchObjects
from bims.api_views.validate_object import ValidateObject
from bims.api_views.reject_collection_data import RejectCollectionData
from bims.api_views.get_biorecord import (
    GetBioRecordDetail,
    GetBioRecords
)
from bims.api_views.non_validated_record import GetNonValidatedRecords
from bims.api_views.hide_popup_info_user import HidePopupInfoUser
from bims.api_views.send_notification_to_validator import \
    SendNotificationValidation
from bims.views.locate import filter_farm_ids_view, get_farm_view
from bims.api_views.user_boundary import UserBoundaryList
from bims.api_views.documents import DocumentList
from bims.api_views.module_summary import ModuleSummary

urlpatterns = [
    url(r'^location-type/(?P<pk>[0-9]+)/allowed-geometry/$',
        LocationTypeAllowedGeometryDetail.as_view()),
    url(r'^location-site/cluster/$', LocationSiteClusterList.as_view()),
    url(r'^location-site/$', LocationSiteList.as_view()),
    url(r'^location-site-detail/$',
        LocationSiteDetail.as_view(),
        name='location-site-detail'),
    url(r'^taxon/(?P<pk>[0-9]+)/$',
        TaxonDetail.as_view()),
    url(r'^list-taxon/$',
        TaxonSimpleList.as_view()),
    url(r'^list-taxon-for-document/(?P<docid>[0-9]+)/$',
        TaxonForDocument.as_view()),
    url(r'^cluster/(?P<administrative_level>\w+)/$',
        ClusterList.as_view()),
    url(r'^collection/extent/$',
        GetCollectionExtent.as_view()),
    url(r'^collection/cluster/$',
        ClusterCollection.as_view()),
    url(r'^collection/download/$',
        CollectionDownloader.as_view()),
    url(r'^search/$',
        SearchObjects.as_view(), name='search-api'),
    url(r'^boundary/geojson$',
        BoundaryGeojson.as_view(), name='boundary-geojson'),
    url(r'^list-boundary/$',
        BoundaryList.as_view(), name='list-boundary'),
    url(r'^list-user-boundary/$',
        UserBoundaryList.as_view(), name='list-user-boundary'),
    url(r'^list-collector/$',
        CollectorList.as_view(), name='list-collector'),
    url(r'^list-category/$',
        CategoryList.as_view(), name='list-date-category'),
    url(r'^list-reference/$',
        ReferenceList.as_view(), name='list-reference'),
    url(r'^list-entry-reference/$',
        ReferenceEntryList.as_view(), name='list-entry-reference'),
    url(r'^list-documents/$',
        DocumentList.as_view(), name='list-documents'),
    url(r'^list-non-biodiversity/$',
        NonBiodiversityLayerList.as_view(),
        name='list-non-biodiversity-layer'),
    url(r'^validate-object/$',
        ValidateObject.as_view(), name='validate-object'),
    url(r'^reject-collection-data/$',
        RejectCollectionData.as_view(), name='reject-collection-data'),
    url(r'^get-bio-object/$',
        GetBioRecordDetail.as_view(), name='get-bio-object'),
    url(r'^get-bio-records/$',
        GetBioRecords.as_view(), name='get-bio-records'),
    url(r'^get-unvalidated-records/$',
        GetNonValidatedRecords.as_view(), name='get-unvalidated-records'),
    url(r'^send-email-validation/$',
        SendNotificationValidation.as_view(), name='send-email-validation'),
    url(r'^filter-farm-id/$',
        filter_farm_ids_view, name='filter-farm-id'),
    url(r'^get-farm/(?P<farm_id>[\w-]+)/$',
        get_farm_view, name='get-farm'),
    url(r'hide-popup-info/$',
        HidePopupInfoUser.as_view(), name='hide-popup-user'),
    url(r'^list-reference-category/$',
        ReferenceCategoryList.as_view(), name='list-reference-category'),
    url(r'^docs/', include_docs_urls(title='BIMS API')),
    url(r'^module-summary/$',
        ModuleSummary.as_view(),
        name='module-summary')
]
