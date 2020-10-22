"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import re_path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from geonode.urls import urlpatterns as geonode_urlpatterns
from bims.views.documents import document_metadata, BimsDocumentUploadView


# GeoNode has to be in root url conf.
# It cannot be included in include() function because it contains i18n urls
urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^contact/', include('contactus.urls')),
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    url(r'^', include('bims.urls')),
    url(r'^', include('bims_theme.urls')),
    url(r'^sass/', include('sass.urls')),
    url(r'^api/v1/celery-inspect/', include('celery_inspect.urls')),
    url(r'^bibliography/',
        include(('td_biblio.urls', 'bibliography'),
                namespace = 'td_biblio')),
    url(r'^', include('example.urls')),

    # prometheus monitoring
    url(r'', include('django_prometheus.urls')),
    url(r'^documents/(?P<docid>\d+)/metadata$',
        document_metadata,
        name='document_metadata'),
    url(r'^documents/upload/?$', login_required(
        BimsDocumentUploadView.as_view()),
        name='document_upload'),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^geonode/?$',
        TemplateView.as_view(template_name='site_index.html'),
        name='home'),
    re_path(r'^wagtail-documents/', include(wagtaildocs_urls)),
    re_path(r'^cms/', include(wagtailadmin_urls)),
]

for geonode_pattern in geonode_urlpatterns:
    try:
        if 'admin' in geonode_pattern.app_dict:
            geonode_urlpatterns.remove(geonode_pattern)
    except AttributeError:
        continue

urlpatterns += geonode_urlpatterns

urlpatterns += [
    url('^admin/', admin.site.urls),
    re_path(r'^', include(wagtail_urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
