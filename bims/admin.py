# coding=utf-8

from django.contrib.gis import admin
from ordered_model.admin import OrderedModelAdmin
from django import forms
from bims.models import (
    LocationType,
    LocationSite,
    IUCNStatus,
    Taxon,
    Survey,
    LocationContext,
    Boundary,
    BoundaryType,
    Cluster,
    CarouselHeader
)


class LocationSiteForm(forms.ModelForm):
    class Media:
        css = {}
        js = (
            '/static/libs/jquery/jquery-3.3.1.min.js',
            '/static/js/forms/location-site-admin-form.js')


class LocationSiteAdmin(admin.GeoModelAdmin):
    form = LocationSiteForm
    default_zoom = 5
    default_lat = -30
    default_lon = 25


class IUCNStatusAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'sensitive')


class TaxonAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'author', 'iucn_status')


class BoundaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('type',)
    ordering = ('type', 'name')


class ClusterAdmin(admin.ModelAdmin):
    list_display = ('boundary', 'module')
    list_filter = ('boundary', 'module')


class CarouselHeaderAdmin(OrderedModelAdmin):
    list_display = ('order', 'description', 'banner', 'move_up_down_links')


admin.site.register(LocationSite, LocationSiteAdmin)
admin.site.register(LocationType)
admin.site.register(IUCNStatus, IUCNStatusAdmin)
admin.site.register(Taxon, TaxonAdmin)
admin.site.register(Survey)
admin.site.register(LocationContext)

admin.site.register(Boundary, BoundaryAdmin)
admin.site.register(BoundaryType, admin.ModelAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(CarouselHeader, CarouselHeaderAdmin)
