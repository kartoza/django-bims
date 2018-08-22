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

from geonode.urls import urlpatterns as geonode_urlpatterns


# GeoNode has to be in root url conf.
# It cannot be included in include() function because it contains i18n urls
urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^contact/', include('contactus.urls')),
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    url(r'^', include('bims.urls')),
    url(r'^bibliography/',
        include(('td_biblio.urls', 'bibliography'),
                namespace = 'td_biblio')),

    url(r'^', include('reports.urls')),

    url(r'^', include('example.urls')),

    # prometheus monitoring
    url(r'', include('django_prometheus.urls')),

    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^geonode/?$',
        TemplateView.as_view(template_name='site_index.html'),
        name='home'),
]

urlpatterns += geonode_urlpatterns

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
