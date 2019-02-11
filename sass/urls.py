from django.conf.urls import url
from sass.views.sass_form import SassFormView
from sass.views.sass_list import SassListView
from sass.views.sass_dashboard import SassDashboardView


urlpatterns = [
    url(r'^(?P<site_id>\d+)/$', SassFormView.as_view(), name='sass-form-page'),
    url(r'^update/(?P<sass_id>\d+)/$',
        SassFormView.as_view(),
        name='sass-update-page'),
    url(r'^list/$', SassListView.as_view(), name='sass-list-page'),
    url(r'^dashboard/(?P<site_id>\d+)/$',
        SassDashboardView.as_view(),
        name='sass-dashboard-single-site'),
]
