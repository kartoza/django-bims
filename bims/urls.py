# coding=utf-8

from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, path, include, re_path
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from bims.api_views.unpublished_data import UnpublishedData
from bims.views.download_occurrence_template import download_occurrence_template
from bims.views.edit_taxon_view import EditTaxonView
from bims.views.physico_chemical_upload import PhysicoChemicalUploadView
from bims.views.proxy import proxy_request

from bims.views.map import MapPageView
from bims.views.thermal_dashboard import ThermalDashboardView
from bims.views.tracking import dashboard
from bims.views.landing_page import landing_page_view

from bims.api_views.collection import (
    CollectionDownloader,
)

from bims.api_views.get_feature_info import GetFeatureInfo
from bims.api_views.database_record import DatabaseRecordsList
from bims.views.links import LinksCategoryView
from bims.views.activate_user import activate_user
from bims.views.csv_upload import CsvUploadView
from bims.views.taxa_upload import TaxaUploadView
from bims.views.collections_upload import CollectionsUploadView
from bims.views.boundary_upload import (
    ShapefileUploadView,
    process_shapefiles,
    process_user_boundary_shapefiles,
    process_user_boundary_geojson,
)
from bims.views.documents import SourceReferenceBimsDocumentUploadView
from bims.views.under_development import UnderDevelopmentView
from bims.views.download_csv_taxa_list import (
    download_csv_taxa_list, DownloadPdfTaxaList
)
from bims.views.autocomplete_search import (
    autocomplete,
    user_autocomplete,
    data_source_autocomplete,
    species_autocomplete,
    site_autocomplete,
    abiotic_autocomplete,
    location_context_value_autocomplete
)
from bims.views.collections_form import (
    FishFormView,
    InvertFormView,
    AlgaeFormView,
    ModuleFormView
)
from bims.views.location_site import (
    LocationSiteFormView,
    LocationSiteFormUpdateView,
    LocationSiteFormDeleteView,
    NonValidatedSiteView,
    SiteLocationDetailView
)
from bims.views.wetland_site import WetlandSiteFormView
from bims.views.source_reference_form import SourceReferenceView
from bims.views.bug_report import BugReportView
from bims.views.wetland_feedback import WetlandFeedbackView
from bims.views.abiotic_form import AbioticFormView
from bims.views.svg_to_pdf import svg_to_pdf
from bims.api_views.delete_collection_data import CollectionDeleteApiView
from bims.views.documents import BimsDocumentUpdateView
from bims.views.site_visit import (
    SiteVisitUpdateView,
    SiteVisitListView,
    SiteVisitDetailView,
    SiteVisitDeleteView
)
from bims.views.taxa_management import TaxaManagementView
from bims.views.dashboard_management import DashboardManagementView
from bims.views.harvest_collection_data import HarvestCollectionView
from bims.views.source_reference import (
    SourceReferenceListView,
    EditSourceReferenceView,
    AddSourceReferenceView,
    DeleteSourceReferenceView
)
from bims.views.profile import ProfileView, moderator_contacted
from bims.views.backups_management import BackupsManagementView
from bims.views.summary_report import SummaryReportView
from bims.views.download_request import DownloadRequestListView
from bims.views.custom_contact_us import CustomContactUsView
from bims.views.water_temperature import WaterTemperatureView, \
    WaterTemperatureUploadView, WaterTemperatureValidateView, \
    WaterTemperatureSiteView, WaterTemperatureEditView
from bims.views.download_taxa_template import download_taxa_template
from bims.views.physico_chemical import PhysicoChemicalView, \
    PhysicoChemicalSiteView
from bims.views.harvest_gbif_species import HarvestGbifSpeciesView
from bims.views.layer_upload import (
    BoundaryUploadView,
    UserBoundaryUploadView
)

urlpatterns = [
    re_path(r'^$', landing_page_view, name='landing-page'),
    re_path(r'^map/$', MapPageView.as_view(), name='map-page'),
    re_path(r'^upload/$', CsvUploadView.as_view(),
            name='csv-upload'),
    re_path(r'^upload-taxa/$', TaxaUploadView.as_view(),
            name='csv-upload-taxa'),
    re_path(r'^upload_shp/$', ShapefileUploadView.as_view(),
            name='shapefile-upload'),
    re_path(r'^process_shapefiles/$', process_shapefiles,
            name='process_shapefiles'),
    re_path(r'^process_user_boundary_shapefiles/$',
            process_user_boundary_shapefiles,
            name='process_user_boundary_shapefiles'),
    re_path(r'^process_user_boundary_geojson/$',
            process_user_boundary_geojson,
            name='process_user_boundary_geojson'),
    re_path(r'^links/$', LinksCategoryView.as_view(), name='link_list'),
    re_path(r'^activate-user/(?P<username>[\w-]+)/$',
            activate_user, name='activate-user'),
    re_path(r'^under-development/$',
            UnderDevelopmentView.as_view(), name='under-development'),
    re_path(r'^tracking/$', dashboard, name='tracking-dashboard'),
    re_path(r'^get_feature/$',
            GetFeatureInfo.as_view(),
            name='get-feature'),
    re_path(r'^collection/check_process/$',
            CollectionDownloader.as_view()),
    re_path(r'^download-csv-taxa-list/$',
            download_csv_taxa_list,
            name='taxa-list-download'),
    re_path(r'^download-pdf-taxa-list/$',
            DownloadPdfTaxaList.as_view(),
            name='taxa-list-pdf-download'),
    re_path(r'^autocomplete/$', autocomplete, name='autocomplete-search'),
    re_path(r'^user-autocomplete/$',
            user_autocomplete,
            name='user-autocomplete-search'),
    re_path(r'^species-autocomplete/$',
            species_autocomplete,
            name='species-autocomplete-search'),
    re_path(r'^data-source-autocomplete/$',
            data_source_autocomplete,
            name='data-source-autocomplete-search'),
    re_path(r'^location-site-autocomplete/$',
            site_autocomplete,
            name='location-site-autocomplete-search'),
    re_path(r'^abiotic-autocomplete/$',
            abiotic_autocomplete,
            name='abiotic-autocomplete-search'),
    re_path(r'^location-context-autocomplete/$',
            location_context_value_autocomplete,
            name='location-context-autocomplete'),
    re_path(r'^bims_proxy/(?P<path>.*)', proxy_request),
    re_path(r'^fish-form/$', FishFormView.as_view(), name='fish-form'),
    re_path(r'^invert-form/$', InvertFormView.as_view(), name='invert-form'),
    re_path(r'^algae-form/$', AlgaeFormView.as_view(), name='algae-form'),
    re_path(r'^module-form/$', ModuleFormView.as_view(), name='module-form'),
    re_path(r'^source-reference-form/$', SourceReferenceView.as_view(),
            name='source-reference-form'),
    re_path(r'^source-reference/database/',
            DatabaseRecordsList.as_view(),
            name='source-reference-database'),
    re_path(r'^source-reference/document/upload$',
            SourceReferenceBimsDocumentUploadView.as_view(),
            name='source-reference-document-upload'),
    re_path(r'^location-site-form/add/$',
            LocationSiteFormView.as_view(),
            name='location-site-form'),
    path('add-wetland-site/',
         WetlandSiteFormView.as_view(),
         name='add-wetland-site'),
    re_path(r'^location-site-form/update/$',
            LocationSiteFormUpdateView.as_view(),
            name='location-site-update-form'),
    re_path(r'^location-site-form/delete/(?P<site_id>\d+)/$',
            LocationSiteFormDeleteView.as_view(),
            name='location-site-delete-form'),
    re_path(r'^bug-report/$', BugReportView.as_view(),
            name='bug-report'),
    re_path(r'^wetland-feedback/$', WetlandFeedbackView.as_view(),
            name='wetland-feedback'),
    re_path(r'^abiotic/$', AbioticFormView.as_view(),
            name='abiotic-form'),
    re_path(r'^svg_to_pdf/$', svg_to_pdf, name='svg-to-pdf'),
    re_path(r'^collection/delete/(?P<col_id>\d+)/$',
            CollectionDeleteApiView.as_view(),
            name='collection-delete'),
    re_path(r'^bims-document/(?P<pk>\d+)/$',
            BimsDocumentUpdateView.as_view(),
            name='bims-document-update-view'),
    re_path(r'^site-visit/update/(?P<sitevisitid>\d+)/$',
            login_required(SiteVisitUpdateView.as_view()),
            name='site-visit-update'),
    re_path(r'^site-visit/list/$',
            SiteVisitListView.as_view(),
            name='site-visit-list'),
    re_path(r'^site-visit/detail/(?P<sitevisitid>\d+)/$',
            SiteVisitDetailView.as_view(),
            name='site-visit-detail'),
    re_path(r'^site-visit/delete/(?P<sitevisitid>\d+)/$',
            SiteVisitDeleteView.as_view()),
    re_path(r'^taxa-management/$',
            TaxaManagementView.as_view(),
            name='taxa-management'),
    re_path(r'^backups-management/$',
            BackupsManagementView.as_view()),
    re_path(r'^dashboard-management/$',
            DashboardManagementView.as_view()),
    re_path(r'^upload-collections/$', CollectionsUploadView.as_view(),
            name='upload-collections'),
    re_path(r'^upload-physico-chemical/$', PhysicoChemicalUploadView.as_view(),
            name='upload-physico-chemical'),
    re_path(r'^harvest-collections/$', HarvestCollectionView.as_view(),
            name='harvest-collections'),
    path('harvest-species/', HarvestGbifSpeciesView.as_view(), name='harvest-gbif-species'),
    re_path(r'^source-references/$', SourceReferenceListView.as_view(),
            name='source-references'),
    re_path(r'^delete-source-reference/$', DeleteSourceReferenceView.as_view(),
            name='delete-source-reference'),
    re_path(r'^edit-source-reference/(?P<pk>\d+)/$',
            EditSourceReferenceView.as_view(),
            name='edit-source-reference'),
    re_path(r'^add-source-reference/$',
            AddSourceReferenceView.as_view(),
            name='add-source-reference'),
    re_path(r'^summary-report/$', SummaryReportView.as_view(),
            name='summary-report'),
    re_path(r'^profile/(?P<slug>\w+)/$', ProfileView.as_view(),
            name='profile'),
    re_path(r'^download-request/$', DownloadRequestListView.as_view(),
            name='download-request'),
    re_path(r'^profile/$',
            login_required(lambda request: RedirectView.as_view(
                url=reverse_lazy('profile', kwargs={
                    'slug': request.user.username
                }), permanent=False)(request)), name='user-profile'),
    re_path(r'^contact/$', CustomContactUsView.as_view(),
            name='contact'),
    re_path(r'^contact/success/$', TemplateView.as_view(
        template_name='contactus/contact_success.html'),
            {}, 'contactus-success'),
    re_path(r'^nonvalidated-site/$',
            NonValidatedSiteView.as_view(), name='nonvalidated-site'),
    re_path(r'^nonvalidated-site/detail/(?P<locationsiteid>\d+)/$',
            SiteLocationDetailView.as_view(), name='nonvalidated-site'),
    re_path(r'^source-reference/unpublished/',
            UnpublishedData.as_view(),
            name='source-reference-unpublished'),
    re_path(r'^download-taxa-template/',
            download_taxa_template,
            name='download-taxa-template'),
    re_path(r'^download-occurrence-template/',
            download_occurrence_template,
            name='download-occurrence-template'),
    re_path(r'^water-temperature-form/$',
            WaterTemperatureView.as_view(),
            name='water-temperature-form'),
    re_path(r'^physico-chemical-form/$',
            PhysicoChemicalView.as_view(),
            name='physico-chemical-form'),
    re_path(r'^water-temperature-form/edit/$',
            WaterTemperatureEditView.as_view(),
            name='water-temperature-edit-form'),
    re_path(r'^upload-water-temperature/$',
            WaterTemperatureUploadView.as_view(),
            name='upload-water-temperature'),
    re_path(r'^validate-water-temperature/$',
            WaterTemperatureValidateView.as_view(),
            name='validate-water-temperature'),
    re_path(r'^water-temperature/(?P<site_id>\d+)/$',
            WaterTemperatureSiteView.as_view(),
            name='water-temperature-site'),
    re_path(r'^water-temperature/(?P<site_id>\d+)/(?P<year>\d{4})/$',
            WaterTemperatureSiteView.as_view(),
            name='water-temperature-site'),
    re_path(r'^physico-chemical/(?P<site_id>\d+)/$',
            PhysicoChemicalSiteView.as_view(),
            name='physico-chemical-site'),
    # Account
    re_path(
        r'^account/moderation_sent/(?P<inactive_user>[^/]*)$',
        moderator_contacted,
        name='moderator_contacted'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('upload-layer/',
         BoundaryUploadView.as_view(),
         name='layer-upload-view'),
    path('upload-polygon/',
         UserBoundaryUploadView.as_view(),
         name='user-boundary-upload-view'),

    path('taxonomy/edit/<int:taxon_group_id>/<int:id>/',
         EditTaxonView.as_view(),
         name='edit_taxon'),
]

# Api urls
urlpatterns += [  # '',
    re_path(r'^api/',
            include('bims.api_urls')),
]

# Thermals
urlpatterns += [
    re_path(r'^thermal-dashboard/$',
            ThermalDashboardView.as_view(),
            name='thermal-dashboard'),
]
