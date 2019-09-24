# coding=utf-8
from datetime import timedelta
from datetime import date
import json
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters.html import HtmlFormatter
from rangefilter.filter import DateRangeFilter
from preferences.admin import PreferencesAdmin

from django.contrib.admin import SimpleListFilter
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis import admin
from django.contrib import admin as django_admin
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.utils.html import format_html

from geonode.documents.admin import DocumentAdmin
from geonode.documents.models import Document
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
    Taxonomy,
    TaxonGroup,
    VernacularName,
    RiverCatchment,
    FbisUUID,
    Biotope,
    DataSource,
    SpatialScale,
    SpatialScaleGroup,
    SamplingMethod,
    SiteImage,
    SiteSetting,
    BimsDocument,
    ChemicalRecord,
    LocationContext
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


class LocationContextInline(admin.TabularInline):
    model = LocationContext


class LocationContextAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'value')


class LocationSiteAdmin(admin.GeoModelAdmin):
    form = LocationSiteForm
    default_zoom = 5
    default_lat = -30
    default_lon = 25

    readonly_fields = (
        'location_context_prettified',
        'original_geomorphological')

    list_display = (
        'name',
        'site_code',
        'location_type',
        'get_centroid',
        'has_location_context')
    search_fields = ('name', 'site_code', 'legacy_site_code')
    list_filter = (HasLocationContextDocument,)
    raw_id_fields = ('river', )
    list_display_links = ['name', 'site_code']

    actions = ['update_location_context', 'delete_location_context']
    inlines = [LocationContextInline, ]

    def get_readonly_fields(self, request, obj=None):
        return ['original_geomorphological']

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

    def save_model(self, request, obj, form, change):
        if not obj.creator:
            obj.creator = request.user
        if obj.owner and not request.user.is_superuser:
            pass
        obj.save()


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


class PermissionContenTypeFilter(SimpleListFilter):
    title = 'App Label'
    parameter_name = 'content_type_app_label'

    def lookups(self, request, model_admin):
        content_types = []
        app_labels = []
        all_object = model_admin.model.objects.all()
        for permission_object in all_object:
            if permission_object.content_type.app_label not in app_labels:
                app_labels.append(permission_object.content_type.app_label)
                content_types.append(permission_object.content_type)
        return [(c.app_label, c.app_label) for c in content_types]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type__app_label=self.value())
        else:
            return queryset.all()


class PermissionAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'name', 'codename')
    list_filter = ('content_type', 'name', PermissionContenTypeFilter)


class CarouselHeaderAdmin(OrderedModelAdmin):
    list_display = ('order', 'description', 'banner', 'move_up_down_links')


class BiologicalCollectionAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('admin/custom-admin.css',)
        }
    # exclude = ['source_reference',]
    list_display = (
        'taxonomy',
        'category',
        'collection_date',
        'is_validated',
        'is_rejected',
        'collector',
        'owner',
    )
    raw_id_fields = (
        'site',
        'owner',
        'taxonomy'
    )
    list_filter = (
        ('collection_date', DateRangeFilter),
        'taxonomy',
        'category'
    )
    search_fields = (
        'taxonomy__scientific_name',
        'taxonomy__canonical_name',
        'original_species_name',
        'uuid'
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
    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)
    model = BimsProfile


# Inherits from GeoNode ProfileCreationForm
class UserCreateForm(ProfileCreationForm):
    class Meta:
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


class SassAccreditedStatusFilter(SimpleListFilter):
    title = 'Sass accredited status'
    parameter_name = 'sass_accredited'

    def lookups(self, request, model_admin):
        return [
            (True, 'Accredited'),
            (False, 'Not accredited')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(
                bims_profile__sass_accredited_date_to__gte=date.today()
            )
        elif self.value() == 'False':
            return queryset.filter(
                bims_profile__sass_accredited_date_to__lte=date.today()
            )
        return queryset


# Inherits from GeoNode's ProfileAdmin page
class CustomUserAdmin(ProfileAdmin):
    add_form = UserCreateForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'organization')}),
        ('Profiles',
         {'classes': ('placeholder bims_profile-group',), 'fields': ()}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    inlines = [ProfileInline]
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name',
                       'last_name', 'email', 'is_staff', 'is_superuser',
                       'groups',),
        }),
    )
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'sass_accredited_status'
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        SassAccreditedStatusFilter
    )

    def sass_accredited_status(self, obj):
        false_response = format_html(
            '<img src="/static/admin/img/icon-no.svg" alt="False">')
        true_response = format_html(
                '<img src="/static/admin/img/icon-yes.svg" alt="True">')
        try:
            profile = BimsProfile.objects.get(user=obj)
            valid_to = profile.sass_accredited_date_to
            if not valid_to:
                return '-'
            # Check if it is still valid
            if date.today() > valid_to:
                return false_response
            else:
                return true_response
        except BimsProfile.DoesNotExist:
            return '-'

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

    search_fields = (
        'scientific_name',
    )


class VernacularNameAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'language',
        'source'
    )


class RiverCatchmentAdmin(admin.ModelAdmin):

    list_display = (
        'key',
        'value',
        'parent',
    )

    list_filter = (
        'key',
    )


class FbisUUIDAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'content_type', 'content_object')
    list_filter = ('content_type',)
    ordering = ('content_type', 'uuid')
    search_fields = ('uuid', )


class SassBiotopeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'display_order',
        'biotope_form',
        'taxon_group',
    )
    list_filter = (
        'name',
    )
    ordering = (
        'name',
        'display_order',
        'biotope_form'
    )


class DataSourceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category'
    )


class SpatialScaleAdmin(admin.ModelAdmin):
    list_display = (
        'query',
        'name',
        'type',
        'group'
    )
    list_filter = (
        'group',
    )
    search_fields = (
        'query',
    )


class SpatialScaleGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'parent'
    )


class SamplingMethodAdmin(admin.ModelAdmin):
    list_display = (
        'sampling_method',
        'effort_measure'
    )


class SiteImageAdmin(admin.ModelAdmin):
    list_display = (
        'site',
        'image'
    )


class BimsDocumentInline(admin.StackedInline):
    model = BimsDocument
    classes = ('collapse open',)
    inline_classes = ('collapse open',)


class BimsDocumentAdmin(DocumentAdmin):
    inlines = [BimsDocumentInline]


class ChemicalRecordAdmin(admin.ModelAdmin):
    list_display = (
        'value',
        'chem',
        'date',
        'location_site'
    )
    raw_id_fields = (
        'location_site',
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
admin.site.register(Taxonomy, TaxonIdentifierAdmin)
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
admin.site.register(DataSource, DataSourceAdmin)

admin.site.register(ReferenceLink, ReferenceLinkAdmin)
admin.site.register(VernacularName, VernacularNameAdmin)
admin.site.register(RiverCatchment, RiverCatchmentAdmin)
admin.site.register(FbisUUID, FbisUUIDAdmin)
admin.site.register(Biotope, SassBiotopeAdmin)
admin.site.register(SpatialScale, SpatialScaleAdmin)
admin.site.register(SpatialScaleGroup, SpatialScaleGroupAdmin)
admin.site.register(SamplingMethod, SamplingMethodAdmin)
admin.site.register(SiteImage, SiteImageAdmin)
admin.site.register(SiteSetting, PreferencesAdmin)
admin.site.register(ChemicalRecord, ChemicalRecordAdmin)

# Hide upload files from geonode in admin
admin.site.unregister(Upload)
admin.site.unregister(UploadFile)

# Rerender geonode document admin
admin.site.unregister(Document)
admin.site.register(Document, BimsDocumentAdmin)

if TRACK_PAGEVIEWS:
    admin.site.register(Pageview, PageviewAdmin)

from bims.custom_admin import * # noqa
