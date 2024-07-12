from django.urls import re_path, path

from bims.api_views.checklist import DownloadChecklistAPIView
from bims.api_views.geocontext import (
    IsHarvestingGeocontext, HarvestGeocontextView, ClearHarvestingGeocontextCache,
    GetGeocontextLogLinesView
)
from bims.api_views.taxon_update import UpdateTaxon, ReviewTaxonProposal
from bims.api_views.reference import DeleteRecordsByReferenceId
# from rest_framework.documentation import include_docs_urls
from bims.api_views.boundary import (
    BoundaryList,
    BoundaryGeojson
)
from bims.api_views.celery_status import CeleryStatus
from bims.api_views.duplicate_records import DuplicateRecordsApiView
from bims.api_views.location_site import (
    LocationSiteList,
    LocationSitesSummary,
    LocationSitesCoordinate, GbifIdsDownloader
)
from bims.api_views.location_type import (
    LocationTypeAllowedGeometryDetail
)
from bims.api_views.non_biodiversity_layer import (
    NonBiodiversityLayerList, DownloadLayerData
)
from bims.api_views.search_module import SearchModuleAPIView

from bims.api_views.taxon import (
    TaxonDetail,
    FindTaxon,
    AddNewTaxon,
    TaxaList,
    TaxonTagAutocompleteAPIView, AddTagAPIView
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
from bims.api_views.thermal_data import ThermalDataApiView, WaterTemperatureThresholdApiView
from bims.api_views.validate_object import (
    ValidateSite,
    ValidateTaxon
)
from bims.api_views.reject_object import (
    RejectSite, RejectTaxon, RejectSiteVisit
)
from bims.api_views.taxon_images import TaxonImageList
from bims.api_views.validate_object import ValidateObject
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
from bims.api_views.user_boundary import (
    UserBoundaryList,
    UserBoundaryDetailList,
    UserBoundaryDetail,
    DeleteUserBoundary
)
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
    SingleLocationSiteOverview, MultiLocationSitesBackgroundOverview
)
from bims.api_views.source_collection import SourceCollectionList
from bims.api_views.site_code import GetSiteCode
from bims.api_views.geomorphological_zone import GetGeomorphologicalZone
from bims.api_views.chemical_record import ChemicalRecordDownloader
from bims.api_views.taxa_search_result import TaxaSearchResult
from bims.api_views.river_name import GetRiverName
from bims.download.csv_download import CsvDownload
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
from bims.views.source_reference import SourceReferenceAPIView
from bims.api_views.decision_support_tool import DecisionSupportToolView, \
    DecisionSupportToolList, check_dst_status
from bims.api_views.download_request import (
    DownloadRequestApi
)
from bims.api_views.wetland_data import WetlandDataApiView
from bims.views.cites import TaxaCitesStatusAPIView
from mobile.api_views.taxon_group import TaxonGroupTotalValidated

urlpatterns = [
    re_path(r'^location-type/(?P<pk>[0-9]+)/allowed-geometry/$',
        LocationTypeAllowedGeometryDetail.as_view()),
    re_path(r'^location-site/$', LocationSiteList.as_view()),
    re_path(r'^location-site-detail/$',
        SingleLocationSiteOverview.as_view(),
        name='location-site-detail'),
    re_path(r'^multi-location-sites-overview/$',
        MultiLocationSitesOverview.as_view(),
        name='multi-location-sites-overview'),
    re_path(r'^multi-location-sites-background-overview/$',
        MultiLocationSitesBackgroundOverview.as_view(),
        name='multi-location-sites-background-overview'),
    re_path(r'^location-sites-summary/$',
        LocationSitesSummary.as_view(),
        name='location-sites-summary'),
    re_path(r'^location-sites-endemism-chart-data/$',
        LocationSitesEndemismChartData.as_view(),
        name='location-sites-endemism-chart-data'),
    re_path(r'^location-sites-occurrences-chart-data/$',
        OccurrencesChartData.as_view(),
        name='location-sites-occurrences-chart-data'),
    re_path(r'^location-sites-cons-chart-data/$',
        LocationSitesConservationChartData.as_view(),
        name='location-sites-cons-chart-data'),
    re_path(r'^location-sites-taxa-chart-data/$',
        LocationSitesTaxaChartData.as_view(),
        name='location-sites-taxa-chart-data'),
    re_path(r'^location-sites-coordinate/$',
        LocationSitesCoordinate.as_view(),
        name='location-sites-coordinate'),
    re_path(r'^taxon/(?P<pk>[0-9]+)/$',
        TaxonDetail.as_view()),
    re_path(r'^cluster/(?P<administrative_level>\w+)/$',
        ClusterList.as_view()),
    re_path(r'^collection/download/$',
        CollectionDownloader.as_view()),
    re_path(r'^chemical-record/download/$',
        ChemicalRecordDownloader.as_view()),
    re_path(r'^collection-search/$',
        CollectionSearchAPIView.as_view(), name='collection-search'),
    re_path(r'^search-module/$',
        SearchModuleAPIView.as_view(), name='search-module'),
    re_path(r'^boundary/geojson$',
        BoundaryGeojson.as_view(), name='boundary-geojson'),
    re_path(r'^list-boundary/$',
        BoundaryList.as_view(), name='list-boundary'),
    re_path(r'^list-user-boundary/$',
        UserBoundaryDetailList.as_view(), name='list-user-boundary'),
    re_path(r'^delete-user-boundary/(?P<id>[\w-]+)/$',
        DeleteUserBoundary.as_view(), name='delete_user_boundary'),
    re_path(r'^user-boundaries/$',
        UserBoundaryList.as_view(),
        name='list_user_boundary'),
    re_path(r'^user-boundary/(?P<id>[\w-]+)/$',
        UserBoundaryDetail.as_view(),
        name='detail_user_boundary'),
    re_path(r'^list-collector/$',
        CollectorList.as_view(), name='list-collector'),
    re_path(r'^list-dst/$',
        DecisionSupportToolList.as_view(), name='list-dst'),
    re_path(r'^list-category/$',
        CategoryList.as_view(), name='list-date-category'),
    re_path(r'^list-reference/$',
        ReferenceList.as_view(), name='list-reference'),
    re_path(r'^list-entry-reference/$',
        ReferenceEntryList.as_view(), name='list-entry-reference'),
    re_path(r'^list-documents/$',
        DocumentList.as_view(), name='list-documents'),
    re_path(r'^list-non-biodiversity/$',
        NonBiodiversityLayerList.as_view(),
        name='list-non-biodiversity-layer'),
    re_path(r'^validate-object/$',
        ValidateObject.as_view(), name='validate-object'),
    re_path(r'^reject-site-visit/$',
        RejectSiteVisit.as_view(), name='reject-site-visit'),
    re_path(r'^get-bio-object/$',
        GetBioRecordDetail.as_view(), name='get-bio-object'),
    re_path(r'^get-site-code/$',
        GetSiteCode.as_view(), name='get-site-code'),
    re_path(r'^site-in-country/$',
        SiteInCountry.as_view(), name='site-in-country'),
    re_path(r'^get-river-name/$',
        GetRiverName.as_view(), name='get-river-name'),
    re_path(r'^get-geomorphological-zone/$',
        GetGeomorphologicalZone.as_view(), name='get-geomorphological-zone'),
    re_path(r'^get-bio-records/$',
        GetBioRecords.as_view(), name='get-bio-records'),
    re_path(r'^bio-collection-summary/$',
        BioCollectionSummary.as_view(), name='bio-collection-summary'),
    re_path(r'^get-unvalidated-records/$',
        GetNonValidatedRecords.as_view(), name='get-unvalidated-records'),
    re_path(r'^send-email-validation/$',
        SendNotificationValidation.as_view(), name='send-email-validation'),
    re_path(r'^filter-farm-id/$',
        filter_farm_ids_view, name='filter-farm-id'),
    re_path(r'^get-farm/(?P<farm_id>[\w-]+)/$',
        get_farm_view, name='get-farm'),
    re_path(r'hide-popup-info/$',
        HidePopupInfoUser.as_view(), name='hide-popup-user'),
    re_path(r'^list-reference-category/$',
        ReferenceCategoryList.as_view(), name='list-reference-category'),
    re_path(r'^list-source-collection/$',
        SourceCollectionList.as_view(), name='list-source-collection'),
    # re_path(r'^docs/', include_docs_urls(title='BIMS API')),
    re_path(r'^module-summary/$',
        ModuleSummary.as_view(),
        name='module-summary'),
    re_path(r'^endemism-list/$',
        EndemismList.as_view(),
        name='endemism-list'),
    re_path(r'^spatial-scale-filter-list/$',
        SpatialScaleFilterList.as_view(),
        name='spatial-scale-filter-list'),
    re_path(r'^site-search-result/$',
        SiteSearchResult.as_view(),
        name='site-search-result'),
    re_path(r'^taxa-search-result/$',
        TaxaSearchResult.as_view(),
        name='taxa-search-result'),
    re_path(r'^get-site-by-coord/$',
        SiteByCoord.as_view(), name='get-site-by-coord'),
    re_path(r'^module-list/$',
        ModuleList.as_view(),
        name='module-list'),
    re_path(r'^find-taxon/$',
        FindTaxon.as_view(),
        name='find-taxon'),
    re_path(r'^add-new-taxon/$',
        AddNewTaxon.as_view(),
        name='add-new-taxon'),
    re_path(r'^csv-download/$',
        CsvDownload.as_view(),
        name='csv-download'),
    re_path(r'^upload-status/(?P<session_id>[0-9]+)/$',
        DataUploadStatusView.as_view(),
        name='upload-status'),
    re_path(r'^harvest-status/(?P<session_id>[0-9]+)/$',
        HarvestSessionStatusView.as_view(),
        name='harvest-status'),
    re_path(r'^taxa-list/$',
        TaxaList.as_view(),
        name='taxa-list'),
    re_path(r'^update-taxon/(?P<taxon_id>[0-9]+)/(?P<taxon_group_id>[0-9]+)/$',
        UpdateTaxon.as_view(),
        name='update-taxon'),
    path('review-taxon/<int:taxonomy_update_proposal_id>/',
         ReviewTaxonProposal.as_view(), name='review-taxon-proposal'),
    path('review-taxon/<int:taxon_id>/<int:taxon_group_id>/',
         ReviewTaxonProposal.as_view(), name='review-taxon'),
    re_path(r'^update-taxon-group-order/$',
        UpdateTaxonGroupOrder.as_view(),
        name='update-taxon-group-order'),
    re_path(r'^remove-taxa-from-taxon-group/$',
        RemoveTaxaFromTaxonGroup.as_view(),
        name='remove-taxa-from-taxon-group'),
    re_path(r'^add-taxa-to-taxon-group/$',
        AddTaxaToTaxonGroup.as_view(),
        name='add-taxa-to-taxon-group'),
    re_path(r'^update-taxon-group/$',
        UpdateTaxonGroup.as_view(),
        name='update-taxon-group'),
    re_path(r'^landing-page-summary/$',
        LandingPageSummary.as_view(),
        name='landing-page-summary'),
    re_path(r'^location-context-report/$',
        SummaryReportLocationContextApiView.as_view(),
        name='location-context-report'),
    re_path(r'^summary-general-report/$',
        SummaryReportGeneralApiView.as_view(),
        name='summary-general-report'),
    re_path(r'^location-site-summary-public/$',
        LocationSiteSummaryPublic.as_view(),
        name='location-site-summary-public'),
    re_path(r'^remove-occurrences/$',
        RemoveOccurrencesApiView.as_view(),
        name='remove-occurrences'),
    re_path(r'^validate-location-site/$',
        ValidateSite.as_view(), name='validate-location-site'),
    re_path(r'^validate-taxon/$',
        ValidateTaxon.as_view(), name='validate-taxon'),
    re_path(r'^reject-location-site/$',
        RejectSite.as_view(), name='reject-location-site'),
    re_path(r'^reject-taxon/$',
        RejectTaxon.as_view(), name='reject-taxon'),
    re_path(r'^taxon-images/(?P<taxon>[0-9]+)/$', TaxonImageList.as_view(),
        name='taxon-images'),
    re_path(r'^merge-sites/$',
        MergeSites.as_view(),
        name='merge-sites'),
    re_path(r'^duplicate-records/download/$',
        DuplicateRecordsApiView.as_view(),
        ),
    re_path(r'^thermal-data/$',
        ThermalDataApiView.as_view(),
        ),
    re_path(r'^water-temperature-threshold/$',
        WaterTemperatureThresholdApiView.as_view(),
        ),
    re_path(r'^source-reference-list/$',
        SourceReferenceAPIView.as_view(),
        ),
    re_path(r'^decision-support-tool/$',
        DecisionSupportToolView.as_view(),
        name='decision-support-tool'
        ),
    re_path(r'^dst-status/$',
        check_dst_status,
        name='dst-status'
        ),
    re_path(r'^celery-status/(?P<task_id>[\w-]+)/$',
        CeleryStatus.as_view(),
        name='celery-status'
        ),
    re_path(r'^download-request/$',
        DownloadRequestApi.as_view(),
        name='download-request'
        ),
    re_path(r'^gbif-ids/download/$',
        GbifIdsDownloader.as_view()),
    re_path(r'^checklist/download/$',
        DownloadChecklistAPIView.as_view()),
    path('download-layer-data/<int:layer_id>/<str:query_filter>/',
        DownloadLayerData.as_view(),
        name='download-layer-data'),
    path('delete-records-by-source-reference-id/<int:source_reference_id>/',
         DeleteRecordsByReferenceId.as_view(),
         name='delete-records-by-source-reference-id'),
    re_path(r'^taxon-tag-autocomplete/$',
            TaxonTagAutocompleteAPIView.as_view(),
            name='taxon-tag-autocomplete'),
    path('taxonomy/<int:pk>/add-tag/',
         AddTagAPIView.as_view(),
         name='add-tag-taxon'),
    path('wetland-data/<str:lat>/<str:lon>/',
         WetlandDataApiView.as_view(),
         name='wetland-data'),
    path('taxa-cites-status/',
         TaxaCitesStatusAPIView.as_view(),
         name='taxa-cites-status'),
    path('is-harvesting-geocontext/',
         IsHarvestingGeocontext.as_view(),
         name='is-harvesting-geocontext'),
    path('harvest-geocontext/',
         HarvestGeocontextView.as_view(),
         name='harvest-geocontext'),
    path('clear-harvesting-geocontext-cache/',
         ClearHarvestingGeocontextCache.as_view(),
         name='clear-harvesting-geocontext-cache'),
    path('harvesting-geocontext-logs/',
         GetGeocontextLogLinesView.as_view(),
         name='get_log_lines'),
    path('taxon-group-validated/<int:id>/',
         TaxonGroupTotalValidated.as_view(),
         name='taxon-group-total-validated'),
]
