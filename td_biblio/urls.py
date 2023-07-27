from django.urls import include, re_path
from td_biblio.views.bibliography import (
    EntryListView,
    EntryBatchImportView,
)
from td_biblio.api_views.bibliography import GetBibliographyByDOI

api_urls = [
    re_path(
        '^fetch/by-doi/$',
        GetBibliographyByDOI.as_view(), name='fetch-by-doi'),
]

urlpatterns = [
    re_path('^$', EntryListView.as_view(), name='entry_list'),
    re_path('^import/$', EntryBatchImportView.as_view(), name='import'),
    re_path('^api/', include(api_urls)),
]
