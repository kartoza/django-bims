# coding=utf-8
from datetime import timedelta
import json
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters.html import HtmlFormatter

from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis import admin
from django.contrib import admin as django_admin
from django.core.mail import send_mail

from django.contrib.auth.models import Permission
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models

from geonode.people.admin import ProfileAdmin
from geonode.people.forms import ProfileCreationForm
from geonode.people.models import Profile
from geonode.upload.models import Upload, UploadFile
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
    LinkCategory,
    Link,
    Visitor,
    Pageview,
    ShapefileUploadSession,
    Shapefile,
    NonBiodiversityLayer,
    UserBoundary,
    SearchProcess,
    ReferenceLink,
    Endemism,
    TaxonIdentifier,
    TaxonGroup,
)

from bims.conf import TRACK_PAGEVIEWS
from bims.models.profile import Profile as BimsProfile


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

    readonly_fields = ('location_context_prettified', 'boundary')

    list_display = (
        'name', 'location_type', 'get_centroid', 'has_location_context')
    search_fields = ('name',)
    list_filter = (HasLocationContextDocument,)

    actions = ['update_location_context', 'delete_location_context']

    def get_readonly_fields(self, request, obj=None):
        return ['longitude', 'latitude']

    def has_location_context(self, obj):
        return bool(obj.location_context_document)

    def update_location_context(self, request, queryset):
        """Action method to update selected location contexts."""
        if len(queryset) > 5:
            message = 'You can not update for more than 5 location site.'
            self.message_user(request, message)
            return
        rows_updated = 0
        rows_failed = 0
        error_message = ''
        for location_site in queryset:
            success, message = location_site.update_location_context_document()
            if success:
                rows_updated += 1
                location_site.save()
            else:
                rows_failed += 1
                error_message += (
                    'Failed to update site [%s] because [%s]\n') % (
                    location_site.name, message)

        if rows_updated == 1:
            message_bit = "1 location context"
        else:
            message_bit = "%s location contexts" % rows_updated
        full_message = "%s successfully updated." % message_bit

        if rows_failed > 0:
            error_message_bit = 'There are %s not updated site.' % rows_failed
            error_message_bit += '\n' + error_message
            full_message += '\n' + error_message_bit

        self.message_user(request, full_message)

    def delete_location_context(self, request, queryset):
        """Action method to delete selected location contexts."""
        rows_updated = queryset.update(location_context_document='')
        if rows_updated == 1:
            message_bit = "1 location context"
        else:
            message_bit = "%s location contexts" % rows_updated
        self.message_user(request, "%s successfully deleted." % message_bit)

    update_location_context.short_description = (
        'Update the selected location context documents.')

    delete_location_context.short_description = (
        'Delete the selected location context documents.')

    def location_context_prettified(self, instance):
        """Function to display pretty format of location context."""
        # Convert the data to sorted, indented JSON
        if instance.location_context_document:
            data = json.loads(instance.location_context_document)
            json_data_string = json.dumps(data, indent=2)

            # Get the Pygments formatter
            formatter = HtmlFormatter(style='colorful', noclasses=True)

            # Highlight the data
            response = highlight(json_data_string, JsonLexer(), formatter)

            # Get the stylesheet
            style = "<style>" + formatter.get_style_defs() + "</style><br>"

            # Safe the output
            return mark_safe(style + response)

    location_context_prettified.short_description = 'Pretty Location Context'


class IUCNStatusAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'sensitive', 'iucn_colour')

    def iucn_colour(self, obj):
        return '<div style="background:%s; ' \
               'width: 50px; height: 15px;"></div>' % obj.colour

    iucn_colour.allow_tags = True


class TaxonAdmin(admin.ModelAdmin):
    list_display = (
        'common_name',
        'author',
        'iucn_status',
        'taxon_class',
        'endemism'
    )


class BoundaryAdmin(admin.ModelAdmin):
    list_display = ('code_name', 'name', 'type', 'top_level_boundary')
    list_filter = ('type',)
    ordering = ('type', 'name')


class ClusterAdmin(admin.ModelAdmin):
    list_display = ('boundary', 'module')
    list_filter = ('boundary', 'module')


class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename')
    list_filter = ('name', 'codename')


class CarouselHeaderAdmin(OrderedModelAdmin):
    list_display = ('order', 'description', 'banner', 'move_up_down_links')


class BiologicalCollectionAdmin(admin.ModelAdmin):
    list_filter = ('taxon_gbif_id', 'collection_date', 'category')
    list_display = (
        'original_species_name',
        'category',
        'collection_date',
        'is_validated',
        'is_rejected',
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


class UserBoundaryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user'
    )


class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


admin.site.register(LinkCategory)
admin.site.register(Link, LinkAdmin)


class ProfileInline(admin.StackedInline):
    model = BimsProfile


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
    inlines = [ProfileInline]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name',
                       'last_name', 'email', 'is_staff', 'is_superuser',
                       'groups',),
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


class NonBiodiversityLayerAdmin(OrderedModelAdmin):
    list_display = (
        'order',
        'name',
        'wms_url',
        'wms_layer_name',
        'move_up_down_links')
    list_filter = ('wms_url',)
    ordering = ('order',)


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


class SearchProcessAdmin(admin.ModelAdmin):

    list_display = (
        'file_path',
        'category',
        'finished')


class PageviewAdmin(admin.ModelAdmin):
    date_hierarchy = 'view_time'

    list_display = ('url', 'view_time')


class ReferenceLinkAdmin(admin.ModelAdmin):

    list_display = (
        'collection_record',
        'reference'
    )


class EndemismAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'description'
    )


class TaxonIdentifierAdmin(admin.ModelAdmin):

    list_display = (
        'gbif_key',
        'scientific_name',
        'rank',
        'parent'
    )

    list_filter = (
        'rank',
    )


# Re-register GeoNode's Profile page
admin.site.unregister(Profile)
admin.site.register(Profile, CustomUserAdmin)

admin.site.register(LocationSite, LocationSiteAdmin)
admin.site.register(LocationType)
admin.site.register(IUCNStatus, IUCNStatusAdmin)
admin.site.register(Taxon, TaxonAdmin)
admin.site.register(Endemism, EndemismAdmin)
admin.site.register(Survey)
admin.site.register(NonBiodiversityLayer, NonBiodiversityLayerAdmin)
admin.site.register(TaxonIdentifier, TaxonIdentifierAdmin)
admin.site.register(TaxonGroup)

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
admin.site.register(Permission, PermissionAdmin)

admin.site.register(UserBoundary, UserBoundaryAdmin)
admin.site.register(SearchProcess, SearchProcessAdmin)

admin.site.register(ReferenceLink, ReferenceLinkAdmin)

# Hide upload files from geonode in admin
admin.site.unregister(Upload)
admin.site.unregister(UploadFile)

if TRACK_PAGEVIEWS:
    admin.site.register(Pageview, PageviewAdmin)
