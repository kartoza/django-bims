# coding=utf-8

from django.contrib.auth.decorators import login_required
from django.conf.urls import url, include
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from bims.views.proxy import proxy_request

from bims.views.map import MapPageView
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
from bims.views.shapefile_upload import (
    ShapefileUploadView,
    process_shapefiles,
    process_user_boundary_shapefiles
)
from bims.views.documents import SourceReferenceBimsDocumentUploadView
from bims.views.under_development import UnderDevelopmentView
from bims.views.non_validated_list import NonValidatedObjectsView
from bims.views.non_validated_user_list import NonValidatedObjectsUserView
from bims.views.bio_records_edit import BioRecordsUpdateView
from bims.views.collection_upload import CollectionUploadView
from bims.views.download_csv_taxa_list import (
    download_csv_taxa_list
)
from bims.views.autocomplete_search import (
    autocomplete,
    user_autocomplete,
    data_source_autocomplete,
    species_autocomplete,
    site_autocomplete,
    abiotic_autocomplete
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
    LocationSiteFormDeleteView
)
from bims.views.source_reference_form import SourceReferenceView
from bims.views.bug_report import BugReportView
from bims.views.abiotic_form import AbioticFormView
from bims.views.svg_to_pdf import svg_to_pdf
from bims.api_views.delete_collection_data import CollectionDeleteApiView
from bims.views.documents import BimsDocumentUpdateView
from bims.views.site_visit import (
    SiteVisitUpdateView, SiteVisitListView, SiteVisitDetailView
)
from bims.views.taxa_management import TaxaManagementView
from bims.views.dashboard_management import DashboardManagementView
from bims.views.harvest_collection_data import HarvestCollectionView
from bims.views.source_reference import SourceReferenceListView
from bims.views.profile import ProfileView
from bims.views.backups_management import BackupsManagementView
from bims.views.summary_report import SummaryReportView
from bims.views.download_request import DownloadRequestListView
from bims.api_router import api_router
from bims.views.custom_contact_us import CustomContactUsView


urlpatterns = [
    url(r'^$', landing_page_view, name='landing-page'),
    url(r'^map/$', MapPageView.as_view(), name='map-page'),
    url(r'^upload/$', CsvUploadView.as_view(),
        name='csv-upload'),
    url(r'^upload-taxa/$', TaxaUploadView.as_view(),
        name='csv-upload-taxa'),
    url(r'^upload_shp/$', ShapefileUploadView.as_view(),
        name='shapefile-upload'),
    url(r'^process_shapefiles/$', process_shapefiles,
        name='process_shapefiles'),
    url(r'^process_user_boundary_shapefiles/$',
        process_user_boundary_shapefiles,
        name='process_user_boundary_shapefiles'),
    url(r'^links/$', LinksCategoryView.as_view(), name='link_list'),
    url(r'^activate-user/(?P<username>[\w-]+)/$',
        activate_user, name='activate-user'),
    url(r'^under-development/$',
        UnderDevelopmentView.as_view(), name='under-development'),
    url(r'^nonvalidated-list/$',
        NonValidatedObjectsView.as_view(), name='nonvalidated-list'),

    url(r'^tracking/$', dashboard, name='tracking-dashboard'),
    url(r'^nonvalidated-user-list/$',
        NonValidatedObjectsUserView.as_view(), name='nonvalidated-user-list'),
    url(r'^update/(?P<pk>\d+)/$',
        BioRecordsUpdateView.as_view(), name='update-records'),
    url(r'^upload_collection/$', CollectionUploadView.as_view(),
        name='upload-collection'),
    url(r'^get_feature/$',
        csrf_exempt(GetFeatureInfo.as_view()),
        name='get-feature'),
    url(r'^collection/check_process/$',
        CollectionDownloader.as_view()),
    url(r'^download-csv-taxa-list/$',
        download_csv_taxa_list,
        name='taxa-list-download'),
    url(r'^autocomplete/$', autocomplete, name='autocomplete-search'),
    url(r'^user-autocomplete/$',
        user_autocomplete,
        name='user-autocomplete-search'),
    url(r'^species-autocomplete/$',
        species_autocomplete,
        name='species-autocomplete-search'),
    url(r'^data-source-autocomplete/$',
        data_source_autocomplete,
        name='data-source-autocomplete-search'),
    url(r'^location-site-autocomplete/$',
        site_autocomplete,
        name='location-site-autocomplete-search'),
    url(r'^abiotic-autocomplete/$',
        abiotic_autocomplete,
        name='abiotic-autocomplete-search'),
    url(r'^bims_proxy/(?P<path>.*)', proxy_request),
    url(r'^fish-form/$', FishFormView.as_view(), name='fish-form'),
    url(r'^invert-form/$', InvertFormView.as_view(), name='invert-form'),
    url(r'^algae-form/$', AlgaeFormView.as_view(), name='algae-form'),
    url(r'^module-form/$', ModuleFormView.as_view(), name='module-form'),
    url(r'^source-reference-form/$', SourceReferenceView.as_view(),
        name='source-reference-form'),
    url(r'^source-reference/database/',
        DatabaseRecordsList.as_view(),
        name='source-reference-database'),
    url(r'^source-reference/document/upload$',
        SourceReferenceBimsDocumentUploadView.as_view(),
        name='source-reference-document-upload'),
    url(r'^location-site-form/add/$',
        LocationSiteFormView.as_view(),
        name='location-site-form'),
    url(r'^location-site-form/update/$',
        LocationSiteFormUpdateView.as_view(),
        name='location-site-update-form'),
    url(r'^location-site-form/delete/(?P<site_id>\d+)/$',
        LocationSiteFormDeleteView.as_view(),
        name='location-site-delete-form'),
    url(r'^bug-report/$', csrf_exempt(BugReportView.as_view()),
        name='bug-report'),
    url(r'^abiotic/$', csrf_exempt(AbioticFormView.as_view()),
        name='abiotic-form'),
    url(r'^svg_to_pdf/$', csrf_exempt(svg_to_pdf), name='svg-to-pdf'),
    url(r'^collection/delete/(?P<col_id>\d+)/$',
        CollectionDeleteApiView.as_view(),
        name='collection-delete'),
    url(r'^bims-document/(?P<pk>\d+)/$',
        BimsDocumentUpdateView.as_view(),
        name='bims-document-update-view'),
    url(r'^site-visit/update/(?P<sitevisitid>\d+)/$',
        login_required(SiteVisitUpdateView.as_view())),
    url(r'^site-visit/list/$',
        SiteVisitListView.as_view()),
    url(r'^site-visit/detail/(?P<sitevisitid>\d+)/$',
        SiteVisitDetailView.as_view()),
    url(r'^taxa-management/$',
        TaxaManagementView.as_view()),
    url(r'^backups-management/$',
        BackupsManagementView.as_view()),
    url(r'^dashboard-management/$',
        DashboardManagementView.as_view()),
    url(r'^upload-collections/$', CollectionsUploadView.as_view(),
        name='upload-collections'),
    url(r'^harvest-collections/$', HarvestCollectionView.as_view(),
        name='harvest-collections'),
    url(r'^source-references/$', SourceReferenceListView.as_view(),
        name='source-references'),
    url(r'^summary-report/$', SummaryReportView.as_view(),
        name='summary-report'),
    url(r'^profile/(?P<slug>\w+)/$', ProfileView.as_view(),
        name='profile'),
    url(r'^download-request/$', DownloadRequestListView.as_view(),
        name='download-request'),
    url(r'^profile/$',
        login_required(lambda request: RedirectView.as_view(
            url=reverse_lazy('profile', kwargs={
                'slug': request.user.username
            }), permanent=False)(request)), name='user-profile'),
    url(r'^contact/$', CustomContactUsView.as_view(),
        name='contact'),
    url(r'^contact/success/$', TemplateView.as_view(
        template_name='contactus/contact_success.html'),
        {}, 'contactus-success'),
]

# Api urls
urlpatterns += [  # '',
    url(r'^api/',
        include('bims.api_urls')),
    url(r'^wagtail-api/v2/', api_router.urls),
]
