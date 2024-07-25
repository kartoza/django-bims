"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from bims.views.documents import BimsDocumentUploadView
from django.urls import re_path


# GeoNode has to be in root url conf.
# It cannot be included in include() function because it contains i18n urls
urlpatterns = [
    re_path(r'^grappelli/', include('grappelli.urls')),
    re_path(r'^accounts/', include('allauth.urls')),
    re_path(r'^pages/', include('django.contrib.flatpages.urls')),
    re_path(r'^', include('bims.urls')),
    re_path(r'^mobile/', include('mobile.urls')),
    re_path(r'^', include('bims_theme.urls')),
    re_path(r'^', include('pesticide.urls')),
    re_path(r'^sass/', include('sass.urls')),
    re_path(r'^bibliography/',
        include(('td_biblio.urls', 'bibliography'),
                namespace = 'td_biblio')),

    # prometheus monitoring
    # re_path(r'', include('django_prometheus.urls')),
    re_path(r'^documents/upload/?$', login_required(
        BimsDocumentUploadView.as_view()),
        name='document_upload'),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    re_path(r'^geonode/?$',
        TemplateView.as_view(template_name='site_index.html'),
        name='home'),
]

urlpatterns += [
    re_path('^admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
