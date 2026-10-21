# coding=utf-8
"""URL routes for the OGC API - Features endpoints.

Mounted at /ogc/layers/<token>/ in core/urls.py.
"""
from django.urls import path

from bims.api_views.ogc_features import (
    ApiView,
    CollectionsView,
    CollectionView,
    ConformanceView,
    ItemsView,
    ItemView,
    LandingPageView,
)

ROUTES = [
    ('', LandingPageView, 'ogc-landing-page'),
    ('api/', ApiView, 'ogc-api'),
    ('conformance/', ConformanceView, 'ogc-conformance'),
    ('collections/', CollectionsView, 'ogc-collections'),
    ('collections/<str:collection_id>/', CollectionView, 'ogc-collection'),
    (
        'collections/<str:collection_id>/items/',
        ItemsView, 'ogc-items'),
    (
        'collections/<str:collection_id>/items/<uuid:item_id>/',
        ItemView, 'ogc-item'),
]

# The canonical URLs end with a slash. The OGC API - Features paths do not,
# and some clients do not follow redirects, so serve both. The landing page
# without a slash is routed in core/urls.py.
urlpatterns = []
for route, view, name in ROUTES:
    urlpatterns.append(path(route, view.as_view(), name=name))
    if route:
        urlpatterns.append(path(route.rstrip('/'), view.as_view()))
