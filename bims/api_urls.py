from django.conf.urls import url
from rest_framework.documentation import include_docs_urls
from bims.api_views.boundary import (
    BoundaryList,
    BoundaryGeojson
)
from bims.api_views.location_site import (
    LocationSiteList,
    LocationSiteClusterList,
    LocationSitesSummary,
    LocationSitesCoordinate
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
    CollectionDownloader,
    ClusterCollection
)
from bims.api_views.collector import CollectorList
from bims.api_views.reference_category import ReferenceCategoryList
from bims.api_views.category_filter import CategoryList
from bims.api_views.reference_list import ReferenceList, ReferenceEntryList
from bims.api_views.search import SearchAPIView
from bims.api_views.validate_object import ValidateObject
from bims.api_views.reject_collection_data import RejectCollectionData
from bims.api_views.get_biorecord import (
    GetBioRecordDetail,
    GetBioRecords,
    BioCollectionSummary
)
from bims.api_views.non_validated_record import GetNonValidatedRecords
from bims.api_views.hide_popup_info_user import HidePopupInfoUser
from bims.api_views.send_notification_to_validator import \
    SendNotificationValidation
from bims.views.locate import filter_farm_ids_view, get_farm_view
from bims.api_views.user_boundary import UserBoundaryList
from bims.api_views.documents import DocumentList
from bims.api_views.module_summary import ModuleSummary
from bims.api_views.endemism import EndemismList
from bims.api_views.site_search_result import SiteSearchResult
from bims.api_views.site_by_coord import SiteByCoord
from bims.api_views.river_catchment import (
    RiverCatchmentList,
    RiverCatchmentTaxonList
)
from bims.api_views.spatial_scale_filter import SpatialScaleFilterList
from bims.api_views.module_list import ModuleList
from bims.api_views.location_site_dashboard import (
    LocationSitesEndemismChartData,
    OccurrencesChartData,
    LocationSitesConservationChartData,
    LocationSitesTaxaChartData
)
from bims.api_views.location_site_overview import (
    MultiLocationSitesOverview,
    SingleLocationSiteOverview
)
from bims.api_views.source_collection import SourceCollectionList
from bims.api_views.site_code import GetSiteCode

urlpatterns = [
    url(r'^location-type/(?P<pk>[0-9]+)/allowed-geometry/$',
        LocationTypeAllowedGeometryDetail.as_view()),
    url(r'^location-site/cluster/$', LocationSiteClusterList.as_view()),
    url(r'^location-site/$', LocationSiteList.as_view()),
    url(r'^location-site-detail/$',
        SingleLocationSiteOverview.as_view(),
        name='location-site-detail'),
    url(r'^multi-location-sites-overview/$',
        MultiLocationSitesOverview.as_view(),
        name='multi-location-sites-overview'),
    url(r'^location-sites-summary/$',
        LocationSitesSummary.as_view(),
        name='location-sites-summary'),
    url(r'^location-sites-endemism-chart-data/$',
        LocationSitesEndemismChartData.as_view(),
        name='location-sites-endemism-chart-data'),
    url(r'^location-sites-occurrences-chart-data/$',
        OccurrencesChartData.as_view(),
        name='location-sites-occurrences-chart-data'),
    url(r'^location-sites-cons-chart-data/$',
        LocationSitesConservationChartData.as_view(),
        name='location-sites-cons-chart-data'),
    url(r'^location-sites-taxa-chart-data/$',
        LocationSitesTaxaChartData.as_view(),
        name='location-sites-taxa-chart-data'),
    url(r'^location-sites-coordinate/$',
        LocationSitesCoordinate.as_view(),
        name='location-sites-coordinate'),
    url(r'^taxon/(?P<pk>[0-9]+)/$',
        TaxonDetail.as_view()),
    url(r'^list-taxon/$',
        TaxonSimpleList.as_view()),
    url(r'^list-taxon-for-document/(?P<docid>[0-9]+)/$',
        TaxonForDocument.as_view()),
    url(r'^cluster/(?P<administrative_level>\w+)/$',
        ClusterList.as_view()),
    url(r'^collection/cluster/$',
        ClusterCollection.as_view()),
    url(r'^collection/download/$',
        CollectionDownloader.as_view()),
    url(r'^search-v2/$',
        SearchAPIView.as_view(), name='search-api-version-2'),
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
    url(r'^get-site-code/$',
        GetSiteCode.as_view(), name='get-site-code'),
    url(r'^get-bio-records/$',
        GetBioRecords.as_view(), name='get-bio-records'),
    url(r'^bio-collection-summary/$',
        BioCollectionSummary.as_view(), name='bio-collection-summary'),
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
    url(r'^list-source-collection/$',
        SourceCollectionList.as_view(), name='list-source-collection'),
    url(r'^docs/', include_docs_urls(title='BIMS API')),
    url(r'^module-summary/$',
        ModuleSummary.as_view(),
        name='module-summary'),
    url(r'^endemism-list/$',
        EndemismList.as_view(),
        name='endemism-list'),
    url(r'^river-catchment-list/$',
        RiverCatchmentList.as_view(),
        name='river-catchment-list'),
    url(r'^spatial-scale-filter-list/$',
        SpatialScaleFilterList.as_view(),
        name='spatial-scale-filter-list'),
    url(r'^site-search-result/$',
        SiteSearchResult.as_view(),
        name='site-search-result'),
    url(r'^get-site-by-coord/$',
        SiteByCoord.as_view(), name='get-site-by-coord'),
    url(r'^river-catchment-taxon-list/$',
        RiverCatchmentTaxonList.as_view(),
        name='river-catchment-taxon-list'),
    url(r'^module-list/$',
        ModuleList.as_view(),
        name='module-list'),
]
