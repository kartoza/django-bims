from django.conf.urls import url, include
from td_biblio.views.bibliography import (
    EntryListView,
    EntryBatchImportView,
)
from td_biblio.api_views.bibliography import GetBibliographyByDOI

api_urls = [
    url(
        '^fetch/by-doi/$',
        GetBibliographyByDOI.as_view(), name='fetch-by-doi'),
]

urlpatterns = [
    url('^$', EntryListView.as_view(), name='entry_list'),
    url('^import/$', EntryBatchImportView.as_view(), name='import'),
    url('^api/', include(api_urls)),
]
