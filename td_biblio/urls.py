# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

app_name = 'td_biblio'
urlpatterns = [
    # Entry List
    url(
        '^$',
        views.EntryListView.as_view(),
        name='entry_list'
    ),
    url(
        '^import/$',
        views.EntryBatchImportView.as_view(),
        name='import'
    ),
]
