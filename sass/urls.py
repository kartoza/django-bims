from django.conf.urls import url
from sass.views.form import FormView
from sass.views.sass_list import SassListView


urlpatterns = [
    url(r'^(?P<site_id>\d+)/$', FormView.as_view(), name='sass-form-page'),
    url(r'^update/(?P<sass_id>\d+)/$',
        FormView.as_view(),
        name='sass-update-page'),
    url(r'^list/$', SassListView.as_view(), name='sass-list-page'),
]
