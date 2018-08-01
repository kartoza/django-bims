# coding=utf-8
from datetime import timedelta

from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis import admin
from django.contrib import admin as django_admin
from django.core.mail import send_mail

from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models

from geonode.people.admin import ProfileAdmin
from geonode.people.forms import ProfileCreationForm
from geonode.people.models import Profile
from ordered_model.admin import OrderedModelAdmin

from ckeditor.widgets import CKEditorWidget

from bims.models import (
    LocationType,
    LocationSite,
    IUCNStatus,
    Taxon,
    Survey,
    Boundary,
    BoundaryType,
    Cluster,
    CarouselHeader,
    BiologicalCollectionRecord,
    Category,
    Link,
    Visitor,
    Pageview,
    ShapefileUploadSession,
    Shapefile,
    NonBiodiversityLayer,
)

from bims.conf import TRACK_PAGEVIEWS


class LocationSiteForm(forms.ModelForm):
    class Media:
        css = {}
        js = (
            '/static/libs/jquery/jquery-3.3.1.min.js',
            '/static/js/forms/location-site-admin-form.js')


class HasLocationContextDocument(django_admin.SimpleListFilter):
    """Filter based on Location Context Document existence."""
    title = 'has_location_context'
    parameter_name = 'has_location_context'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            return queryset.filter(
                location_context_document__isnull=False).exclude(
                location_context_document__exact='')
        elif value == 'No':
            return queryset.filter(models.Q(
                location_context_document__isnull=True) | models.Q(
                location_context_document__exact=''))
        return queryset


class LocationSiteAdmin(admin.GeoModelAdmin):
    form = LocationSiteForm
    default_zoom = 5
    default_lat = -30
    default_lon = 25

    list_display = (
        'name', 'location_type', 'get_centroid', 'has_location_context')
    search_fields = ('name',)
    list_filter = (HasLocationContextDocument,)

    def has_location_context(self, obj):
        return bool(obj.location_context_document)


class IUCNStatusAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'sensitive')


class TaxonAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'author', 'iucn_status')


class BoundaryAdmin(admin.ModelAdmin):
    list_display = ('code_name', 'name', 'type', 'top_level_boundary')
    list_filter = ('type',)
    ordering = ('type', 'name')


class ClusterAdmin(admin.ModelAdmin):
    list_display = ('boundary', 'module')
    list_filter = ('boundary', 'module')


class CarouselHeaderAdmin(OrderedModelAdmin):
    list_display = ('order', 'description', 'banner', 'move_up_down_links')


class BiologicalCollectionAdmin(admin.ModelAdmin):
    list_filter = ('taxon_gbif_id', 'collection_date')
    list_display = (
        'original_species_name',
        'category',
        'collection_date',
        'validated',
        'collector',
        'owner',
    )


class ShapefileInline(admin.TabularInline):

    def shapefile_name(self, obj):
        if obj.shapefile:
            return mark_safe("""<a href="%s" />%s</a>""" % (
                obj.shapefile.fileurl, obj.shapefile.filename))

    model = ShapefileUploadSession.shapefiles.through
    fields = ('shapefile_name', 'shapefile')
    readonly_fields = ('shapefile_name',)


class ShapefileUploadSessionAdmin(admin.ModelAdmin):
    exclude = ('shapefiles', 'token')
    list_display = (
        'uploader',
        'uploaded_at',
        'processed',
    )

    inlines = (ShapefileInline,)


class ShapefileAdmin(admin.ModelAdmin):
    exclude = ('token',)
    list_display = (
        'id',
        'shapefile',
    )


class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


admin.site.register(Category)
admin.site.register(Link, LinkAdmin)


# Inherits from GeoNode ProfileCreationForm
class UserCreateForm(ProfileCreationForm):
    class Meta:
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


# Inherits from GeoNode's ProfileAdmin page
class CustomUserAdmin(ProfileAdmin):
    add_form = UserCreateForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name',
                       'last_name', 'email', 'is_staff', 'is_superuser',
                       'user_permissions'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.is_active = False
        super(CustomUserAdmin, self).save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        scheme = request.scheme
        site = request.get_host()
        data = {
            'firstname': obj.first_name,
            'lastname': obj.last_name,
            'scheme': scheme,
            'site': site,
            'username': obj.username
        }
        send_mail(
            '[BIMS] Activate your new account',
            'Dear {firstname} {lastname},\n\nPlease follow this link '
            'to change your password and to activate your account:\n'
            '{scheme}://{site}/activate-user/{username}/\n\n'
            'Here is your information:\n'
            'Username: {username}\n\n'
            'Kind regards,\nBIMS Team.'.format(
                **data
            ),
            obj.email,
            [obj.email],
            fail_silently=False
        )
        return super(CustomUserAdmin, self).response_add(
            request, obj, post_url_continue)


class NonBiodiversityLayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'wms_url', 'wms_layer_name')
    list_filter = ('wms_url',)
    ordering = ('name',)


# flatpage ckeditor integration
class FlatPageCustomAdmin(FlatPageAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget}
    }


class VisitorAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_time'

    list_display = (
        'session_key',
        'user',
        'start_time',
        'session_over',
        'pretty_time_on_site',
        'ip_address',
        'user_agent')

    list_filter = ('user', 'ip_address')

    def session_over(self, obj):
        return obj.session_ended() or obj.session_expired()

    session_over.boolean = True

    def pretty_time_on_site(self, obj):
        if obj.time_on_site is not None:
            return timedelta(seconds=obj.time_on_site)

    pretty_time_on_site.short_description = 'Time on site'


class PageviewAdmin(admin.ModelAdmin):
    date_hierarchy = 'view_time'

    list_display = ('url', 'view_time')


# Re-register GeoNode's Profile page
admin.site.unregister(Profile)
admin.site.register(Profile, CustomUserAdmin)

admin.site.register(LocationSite, LocationSiteAdmin)
admin.site.register(LocationType)
admin.site.register(IUCNStatus, IUCNStatusAdmin)
admin.site.register(Taxon, TaxonAdmin)
admin.site.register(Survey)
admin.site.register(NonBiodiversityLayer, NonBiodiversityLayerAdmin)

admin.site.register(Boundary, BoundaryAdmin)
admin.site.register(BoundaryType, admin.ModelAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(CarouselHeader, CarouselHeaderAdmin)
admin.site.register(BiologicalCollectionRecord, BiologicalCollectionAdmin)

admin.site.register(ShapefileUploadSession, ShapefileUploadSessionAdmin)
admin.site.register(Shapefile, ShapefileAdmin)

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageCustomAdmin)

admin.site.register(Visitor, VisitorAdmin)
if TRACK_PAGEVIEWS:
    admin.site.register(Pageview, PageviewAdmin)
