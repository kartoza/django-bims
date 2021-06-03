from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
# from rest_framework.documentation import include_docs_urls
from bims.api_views.boundary import (
    BoundaryList,
    BoundaryGeojson
)
from bims.api_views.location_site import (
    LocationSiteList,
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
    FindTaxon,
    AddNewTaxon,
    TaxaList
)
from bims.api_views.cluster import ClusterList
from bims.api_views.collection import (
    CollectionDownloader
)
from bims.api_views.collector import CollectorList
from bims.api_views.reference_category import ReferenceCategoryList
from bims.api_views.category_filter import CategoryList
from bims.api_views.reference_list import ReferenceList, ReferenceEntryList
from bims.api_views.search import CollectionSearchAPIView
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
from bims.api_views.geomorphological_zone import GetGeomorphologicalZone
from bims.api_views.chemical_record import ChemicalRecordDownloader
from bims.api_views.taxa_search_result import TaxaSearchResult
from bims.api_views.river_name import GetRiverName
from bims.api_views.csv_download import CsvDownload
from bims.views.data_upload import DataUploadStatusView
from bims.views.harvest_collection_data import HarvestSessionStatusView
from bims.api_views.taxon_group import (
    UpdateTaxonGroupOrder,
    RemoveTaxaFromTaxonGroup,
    AddTaxaToTaxonGroup,
    UpdateTaxonGroup
)
from bims.api_views.landing_page_summary import LandingPageSummary
from bims.api_views.site_in_country import SiteInCountry
from bims.views.summary_report import *  # noqa

from bims.api_views.location_site_public import (
    LocationSiteSummaryPublic
)
from bims.api_views.remove_occurrences import RemoveOccurrencesApiView
from bims.api_views.merge_sites import MergeSites

urlpatterns = [
    url(r'^location-type/(?P<pk>[0-9]+)/allowed-geometry/$',
        LocationTypeAllowedGeometryDetail.as_view()),
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
    url(r'^cluster/(?P<administrative_level>\w+)/$',
        ClusterList.as_view()),
    url(r'^collection/download/$',
        CollectionDownloader.as_view()),
    url(r'^chemical-record/download/$',
        ChemicalRecordDownloader.as_view()),
    url(r'^collection-search/$',
        CollectionSearchAPIView.as_view(), name='collection-search'),
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
    url(r'^site-in-country/$',
        SiteInCountry.as_view(), name='site-in-country'),
    url(r'^get-river-name/$',
        GetRiverName.as_view(), name='get-river-name'),
    url(r'^get-geomorphological-zone/$',
        GetGeomorphologicalZone.as_view(), name='get-geomorphological-zone'),
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
    # url(r'^docs/', include_docs_urls(title='BIMS API')),
    url(r'^module-summary/$',
        ModuleSummary.as_view(),
        name='module-summary'),
    url(r'^endemism-list/$',
        EndemismList.as_view(),
        name='endemism-list'),
    url(r'^spatial-scale-filter-list/$',
        SpatialScaleFilterList.as_view(),
        name='spatial-scale-filter-list'),
    url(r'^site-search-result/$',
        SiteSearchResult.as_view(),
        name='site-search-result'),
    url(r'^taxa-search-result/$',
        TaxaSearchResult.as_view(),
        name='taxa-search-result'),
    url(r'^get-site-by-coord/$',
        SiteByCoord.as_view(), name='get-site-by-coord'),
    url(r'^module-list/$',
        ModuleList.as_view(),
        name='module-list'),
    url(r'^find-taxon/$',
        FindTaxon.as_view(),
        name='find-taxon'),
    url(r'^add-new-taxon/$',
        csrf_exempt(AddNewTaxon.as_view()),
        name='add-new-taxon'),
    url(r'^csv-download/$',
        CsvDownload.as_view(),
        name='csv-download'),
    url(r'^upload-status/(?P<session_id>[0-9]+)/$',
        DataUploadStatusView.as_view(),
        name='upload-status'),
    url(r'^harvest-status/(?P<session_id>[0-9]+)/$',
        HarvestSessionStatusView.as_view(),
        name='harvest-status'),
    url(r'^taxa-list/$',
        TaxaList.as_view(),
        name='taxa-list'),
    url(r'^update-taxon-group-order/$',
        UpdateTaxonGroupOrder.as_view(),
        name='update-taxon-group-order'),
    url(r'^remove-taxa-from-taxon-group/$',
        RemoveTaxaFromTaxonGroup.as_view(),
        name='remove-taxa-from-taxon-group'),
    url(r'^add-taxa-to-taxon-group/$',
        AddTaxaToTaxonGroup.as_view(),
        name='add-taxa-to-taxon-group'),
    url(r'^update-taxon-group/$',
        UpdateTaxonGroup.as_view(),
        name='update-taxon-group'),
    url(r'^landing-page-summary/$',
        LandingPageSummary.as_view(),
        name='landing-page-summary'),
    url(r'^location-context-report/$',
        SummaryReportLocationContextApiView.as_view(),
        name='location-context-report'),
    url(r'^summary-general-report/$',
        SummaryReportGeneralApiView.as_view(),
        name='summary-general-report'),
    url(r'^location-site-summary-public/$',
        LocationSiteSummaryPublic.as_view(),
        name='location-site-summary-public'),
    url(r'^remove-occurrences/$',
        RemoveOccurrencesApiView.as_view(),
        name='remove-occurrences'),
    url(r'^merge-sites/$',
        MergeSites.as_view(),
        name='merge-sites')
]
