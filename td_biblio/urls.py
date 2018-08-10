from django.conf.urls import url
from td_biblio.views.bibliography import (
    EntryListView,
    EntryBatchImportView,
)

urlpatterns = [
    url('^$', EntryListView.as_view(), name='entry_list'),
    url('^import/$', EntryBatchImportView.as_view(), name='import'),
]
