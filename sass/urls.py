from django.conf.urls import url
from sass.views.sass_form import SassFormView
from sass.views.sass_list import SassListView
from sass.views.sass_dashboard import SassDashboardView
from sass.views.sass_dashboard_multiple import (
    SassDashboardMultipleSitesView,
    SassDashboardMultipleSitesApiView
)
from sass.views.download_sass_data_site import download_sass_data_site


urlpatterns = [
    url(r'^(?P<site_id>\d+)/$', SassFormView.as_view(), name='sass-form-page'),
    url(r'^update/(?P<sass_id>\d+)/$',
        SassFormView.as_view(),
        name='sass-update-page'),
    url(r'^list/$', SassListView.as_view(), name='sass-list-page'),
    url(r'^dashboard/(?P<site_id>\d+)/$',
        SassDashboardView.as_view(),
        name='sass-dashboard-single-site'),
    url(r'^dashboard-multi-sites/$',
        SassDashboardMultipleSitesView.as_view(),
        name='sass-dashboard-multiple-sites'),
    url(r'^dashboard-multi-sites-api/$',
        SassDashboardMultipleSitesApiView.as_view(),
        name='sass-dashboard-multiple-sites-api'),
    url(r'^download-sass-data-site/(?P<site_id>\d+)/$',
        download_sass_data_site,
        name='download-sass-data-site'),
]
