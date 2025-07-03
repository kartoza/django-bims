# coding=utf-8
import csv
import re
from datetime import timedelta
from datetime import date
import json

from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from rangefilter.filter import DateRangeFilter
from preferences.admin import PreferencesAdmin
from preferences import preferences

from django.contrib.admin import SimpleListFilter
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis import admin
from django.contrib import admin as django_admin
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.db.models import Q
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.urls import reverse, path
from django.contrib.auth.forms import UserCreationForm

from django_json_widget.widgets import JSONEditorWidget

from bims.admins.site_setting import SiteSettingAdmin
from bims.api_views.taxon_update import create_taxon_proposal
from bims.enums import TaxonomicGroupCategory
from bims.models.record_type import merge_record_types
from bims.tasks import fetch_vernacular_names
from bims.utils.endemism import merge_endemism
from bims.utils.sampling_method import merge_sampling_method
from bims.tasks.cites_info import fetch_and_save_cites_listing
from bims.helpers.list import chunk_list
from geonode.documents.admin import DocumentAdmin
from geonode.documents.models import Document
from geonode.people.admin import ProfileAdmin
from geonode.people.models import Profile
from ordered_model.admin import OrderedModelAdmin

from django_admin_inline_paginator.admin import TabularInlinePaginated

from bims.models import (
    LocationType,
    LocationSite,
    IUCNStatus,
    Survey,
    SurveyData,
    SurveyDataOption,
    SurveyDataValue,
    Boundary,
    BoundaryType,
    Cluster,
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
    GeocontextSetting,
    BimsDocument,
    ChemicalRecord,
    LocationContext,
    Chem,
    LocationContextGroup,
    LocationContextFilterGroupOrder,
    LocationContextFilter,
    AlgaeData,
    UploadSession,
    DashboardConfiguration,
    HarvestSession,
    generate_site_code,
    location_site_post_save_handler,
    DownloadRequest,
    DownloadRequestPurpose,
    BaseMapLayer,
    RequestLog,
    IngestedData,
    TaxonImage,
    WaterTemperature,
    TaxonExtraAttribute,
    DecisionSupportTool,
    Unit,
    DecisionSupportToolName,
    WaterTemperatureThreshold,
    Notification,
    RecordType,
    Hydroperiod,
    WetlandIndicatorStatus,
    AbundanceType,
    SamplingEffortMeasure,
    TaxonGroupTaxonomy,
    TaxonomyUpdateProposal,
    TaxonomyUpdateReviewer,
    CITESListingInfo,
    ImportTask,
    Invasion,
    FlatPageExtension,
    TagGroup,
    Dataset
)
from bims.models.climate_data import ClimateData
from bims.utils.fetch_gbif import merge_taxa_data
from bims.conf import TRACK_PAGEVIEWS
from bims.models.profile import Profile as BimsProfile, Role
from bims.utils.gbif import search_exact_match, get_species, suggest_search
from bims.utils.location_context import merge_context_group
from bims.utils.user import merge_users
from bims.tasks.location_site import (
    update_location_context as update_location_context_task,
    update_site_code as update_site_code_task
)
from cloud_native_gis.models.layer_upload import LayerUpload


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


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
            return queryset.filter(locationcontext__isnull=False)
        elif value == 'No':
            return queryset.filter(locationcontext__isnull=True)
        return queryset


class LocationContextInline(admin.TabularInline):
    model = LocationContext
    raw_id_fields = ('group',)


class LocationContextAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'value')


class InsideSiteBoundaryFilter(SimpleListFilter):
    """Filter LocationSites by whether they are inside the configured site boundary."""
    title = 'Inside site boundary'
    parameter_name = 'inside_boundary'

    def lookups(self, request, model_admin):
        """Defines the filter choices."""
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        """Returns the filtered queryset based on user's choice."""
        boundary = preferences.SiteSetting.site_boundary

        if not boundary or not boundary.geometry:
            return queryset

        if self.value() == 'yes':
            return queryset.filter(
                geometry_point__within=boundary.geometry)
        elif self.value() == 'no':
            return queryset.exclude(
                geometry_point__within=boundary.geometry)
        return queryset


class LocationSiteAdmin(admin.GeoModelAdmin):
    change_list_template = 'admin/location_site_changelist.html'
    form = LocationSiteForm
    default_zoom = 5
    default_lat = -30
    default_lon = 25

    readonly_fields = (
        'original_geomorphological',)

    list_display = (
        'name',
        'site_code',
        'location_type',
        'get_centroid',
        'geocontext_data_percentage',
        'indicator_thermal')
    search_fields = ('name', 'site_code', 'legacy_site_code')
    list_filter = (
        HasLocationContextDocument,
        InsideSiteBoundaryFilter,
    )
    raw_id_fields = ('river',)
    list_display_links = ['name', 'site_code']

    actions = [
        'update_site_code',
        'update_location_context',
        'delete_location_context',
        'update_location_context_in_background']
    inlines = [LocationContextInline, ]

    def get_readonly_fields(self, request, obj=None):
        return ['original_geomorphological']

    def indicator_thermal(self, obj):
        if obj.watertemperature_set.all().exists():
            return format_html(
                '''
                <a href="/thermal-dashboard/?site-id={0}">Open Thermal Indicator Dashboard</a>
                ''',
                obj.id
            )
        else:
            return '-'

    def geocontext_data_percentage(self, obj):
        raw_keys = preferences.GeocontextSetting.geocontext_keys.split(',')
        key_pairs = []
        for key in raw_keys:
            if ':' in key:
                group_key, layer_id = key.split(':', 1)
                key_pairs.append((group_key, layer_id))
            else:
                key_pairs.append((key, None))

        filters = Q()
        for group_key, layer_id in key_pairs:
            if layer_id:
                filters |= Q(
                    site=obj,
                    group__geocontext_group_key=group_key,
                    group__layer_identifier=layer_id
                )
            else:
                filters |= Q(
                    site=obj,
                    group__geocontext_group_key=group_key
                )

        groups = LocationContext.objects.filter(filters).values(
            'group__geocontext_group_key', 'group__layer_identifier'
        ).distinct()

        matched_count = groups.count()
        total_expected = len(key_pairs)
        percentage = round(matched_count / total_expected * 100) if total_expected > 0 else 0

        return format_html(
            '''
            <progress value="{0}" max="100"></progress>
            <span style="font-weight:bold">{0}%</span>
            ''',
            percentage
        )

    def update_site_code(self, request, queryset):
        """Action to update site code"""
        models.signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite
        )

        if queryset.count() > 10:
            """ Update site code in background """
            update_site_code_task.delay(
                [site.id for site in queryset]
            )
            full_message = (
                'Updating site code for {} sites in background'.format(
                    queryset.count()
                )
            )
            self.message_user(request, full_message)

            return

        for location_site in queryset:
            location_site.site_code, catchments_data = generate_site_code(
                location_site=location_site,
                lat=location_site.latitude,
                lon=location_site.longitude
            )
            location_site.save()

        models.signals.post_save.connect(
            location_site_post_save_handler,
            sender=LocationSite
        )

        self.message_user(
            request,
            'Site codes has been updated for {} sites'.format(
                queryset.count()))

    def update_location_context_in_background(self, request, queryset):
        """Action method to update location context in background"""
        generate_spatial_scale_filter = queryset.count() <= 1
        for location_site in queryset:
            update_location_context_task.delay(
                location_site.id,
                False,
                generate_spatial_scale_filter)
        full_message = (
            'Updating location context for {} sites in background'.format(
                queryset.count()
            )
        )
        self.message_user(request, full_message)

    def update_location_context(self, request, queryset):
        """Action method to update selected location contexts."""
        if len(queryset) > 5:
            message = 'You can not update for more than 5 location sites.'
            self.message_user(request, message)
            return
        rows_updated = 0
        rows_failed = 0
        error_message = ''
        site_names = []
        for location_site in queryset:
            success, message = location_site.update_location_context_document()
            if success:
                rows_updated += 1
                site_names.append(location_site.location_site_identifier)
            else:
                rows_failed += 1
                error_message += (
                                     'Failed to update site [%s] because [%s]\n') % (
                                     location_site.location_site_identifier, message)

        full_message = "%s successfully updated." % ','.join(site_names)

        if rows_failed > 0:
            error_message_bit = 'There are %s not updated site.' % rows_failed
            error_message_bit += '\n' + error_message
            full_message += '\n' + error_message_bit

        self.message_user(request, full_message)

    def delete_location_context(self, request, queryset):
        """Action method to delete selected location contexts."""
        LocationContext.objects.filter(
            site__in=queryset
        ).delete()
        if queryset.count() == 1:
            message_bit = "1 location context"
        else:
            message_bit = "%s location contexts" % queryset.count()
        self.message_user(request, "%s successfully deleted." % message_bit)

    update_location_context.short_description = (
        'Update location context data for selected sites.')

    update_location_context_in_background.short_description = (
        'Update location context data for selected sites in background.')

    delete_location_context.short_description = (
        'Delete location context data for selected sites.')

    def save_model(self, request, obj, form, change):
        if not obj.creator:
            obj.creator = request.user
        if obj.owner and not request.user.is_superuser:
            pass
        obj.save()


class InvasionAdmin(OrderedModelAdmin):
    ordering = ('order',)
    list_display = ('id', 'move_up_down_links', 'category')


class IUCNStatusAdmin(OrderedModelAdmin):
    list_display = ('id', 'get_category_display', 'move_up_down_links',
                    'order', 'sensitive',
                    'iucn_colour', 'national', 'total_species')
    ordering = ('order',)

    list_filter = (
        'national',
    )

    def iucn_colour(self, obj):
        return format_html('<div style="background:%s; ' \
                           'width: 50px; height: 15px;"></div>' % obj.colour)

    def total_species(self, obj):
        total_taxa = Taxonomy.objects.filter(
            iucn_status=obj
        ).count()
        return format_html(
            f'<a href="/admin/bims/taxonomy/?iucn_status__id__exact={obj.id}">'
            f'{total_taxa}</a>'
        )

    iucn_colour.allow_tags = True


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


class BiologicalCollectionAdmin(admin.ModelAdmin, ExportCsvMixin):
    date_hierarchy = 'collection_date'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_staff:
            if not hasattr(
                request.user,
                'bims_profile'
            ):
                return qs.none()
            return qs
        return qs

    class Media:
        css = {
            'all': ('admin/custom-admin.css',)
        }

    # exclude = ['source_reference',]
    list_display = (
        'uuid',
        'taxonomy',
        'get_origin',
        'collection_date',
        'collector',
        'owner',
        'site',
        'abundance_number',
        'biotope',
        'record_type',
        'sampling_method'
    )
    raw_id_fields = (
        'site',
        'owner',
        'taxonomy',
        'source_reference',
        'collector_user',
        'survey'
    )
    list_filter = (
        ('collection_date', DateRangeFilter),
        'taxonomy__origin',
        'record_type__name',
        'sampling_method',
        'ecosystem_type',
        'source_collection',
        'data_type'
    )
    search_fields = (
        'taxonomy__scientific_name',
        'taxonomy__canonical_name',
        'original_species_name',
        'uuid',
        'site__site_code',
        'survey__uuid',
        'upstream_id',
        'source_collection'
    )
    actions = ['export_as_csv']

    def get_search_results(self, request, queryset, search_term):
        uuid_queryset = queryset.filter(
            Q(uuid__icontains=search_term) |
            Q(uuid__icontains=search_term.replace('-', '')),
        )
        if uuid_queryset.count() > 0:
            return uuid_queryset, False
        queryset, use_distinct = super(
            BiologicalCollectionAdmin, self
        ).get_search_results(request, queryset, search_term)
        return queryset, use_distinct

    def get_origin(self, obj):
        try:
            return dict(Taxonomy.CATEGORY_CHOICES)[obj.taxonomy.origin]
        except KeyError:
            return 'Unknown'

    get_origin.short_description = 'Origin'
    get_origin.admin_order_field = 'taxonomy__origin'


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


class BimsProfileAdmin(admin.ModelAdmin):
    model = BimsProfile
    list_display = [
        'user',
        'first_name',
        'last_name',
        'qualifications',
        'sass_accredited_date_from',
        'sass_accredited_date_to']
    search_fields = (
        'user__first_name',
        'user__username'
    )


class ProfileCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username",)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )


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


class UserHasEmailFilter(SimpleListFilter):
    title = 'User has email address'
    parameter_name = 'user_has_email'

    def lookups(self, request, model_admin):
        return [
            (True, 'Yes'),
            (False, 'No')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'False':
            return queryset.filter(
                models.Q(email__isnull=True) |
                models.Q(email='')
            )
        elif self.value() == 'True':
            return queryset.filter(
                email__isnull=False
            ).exclude(email='')
        return queryset


class RoleFilter(SimpleListFilter):
    title = 'Role'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return BimsProfile.ROLE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bims_profile__role__iexact=self.value())
        return queryset


class SignedUpFilter(SimpleListFilter):
    title = 'Signed up'
    parameter_name = 'signed_up'

    def lookups(self, request, model_admin):
        return [
            (True, 'Yes'),
            (False, 'No')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'False':
            return queryset.filter(
                models.Q(email__isnull=True) |
                models.Q(email='')
            )
        elif self.value() == 'True':
            return queryset.filter(
                models.Q(last_login__isnull=False) |
                models.Q(email__isnull=False)
            ).exclude(email='')
        return queryset


# Inherits from GeoNode's ProfileAdmin page
class CustomUserAdmin(ProfileAdmin):
    add_form = UserCreateForm
    change_form_template = 'admin/user_changeform.html'
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
        'organization',
        'role',
        'is_staff',
        'is_active',
        'signed_up',
        'sass_accredited_status',
        'date_joined',
        'last_login'
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        SassAccreditedStatusFilter,
        UserHasEmailFilter,
        'organization',
        SignedUpFilter,
        RoleFilter
    )
    readonly_fields = (
        'password',
    )

    actions = ['merge_users', 'download_csv']

    def download_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        try:
            from StringIO import StringIO  # for Python 2
        except ImportError:
            from io import StringIO  # for Python 3

        f = StringIO()
        writer = csv.writer(f)
        writer.writerow([
            'Username',
            'Email',
            'First Name',
            'Last Name',
            'Organization Name',
            'Role',
            'Staff status',
            'Active',
            'Signed up',
            'SASS Accredited Status',
            'Date joined',
            'Last login'])

        for s in queryset:
            sass_accredited_status = (
                self.sass_accredited_status(s, text_only='True')
            )
            writer.writerow([
                s.username, s.email,
                s.first_name, s.last_name,
                s.organization,
                self.role(s),
                s.is_staff,
                s.is_active,
                self.signed_up(s, text_only='True'),
                sass_accredited_status,
                s.date_joined,
                s.last_login])

        f.seek(0)
        response = HttpResponse(f, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=users.csv'
        return response

    download_csv.short_description = (
        "Download CSV file for selected users"
    )

    def merge_users(self, request, queryset):
        active_user = queryset.filter(is_active=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 user', messages.ERROR
            )
            return
        if not active_user.exists():
            self.message_user(
                request, 'Missing active user', messages.ERROR)
            return
        if active_user.count() > 1:
            self.message_user(
                request, 'There are more than 1 active user',
                messages.ERROR)
            return
        merge_users(
            primary_user=active_user[0],
            user_list=queryset.values_list('id', flat=True)
        )
        self.message_user(request, 'Users has been merged')

    merge_users.short_description = 'Merge users'

    def sass_accredited_status(self, obj):
        false_response = format_html(
            '<img src="/static/admin/img/icon-no.svg" alt="False">')
        true_response = format_html(
            '<img src="/static/admin/img/icon-yes.svg" alt="True">')

    def role(self, obj):
        try:
            profile = BimsProfile.objects.get(user=obj)
            role = [(v) for k, v in BimsProfile.ROLE_CHOICES if k == profile.role]
            return role[0] if len(role) > 0 else '-'
        except BimsProfile.DoesNotExist:
            return '-'

    role.admin_order_field = 'bims_profile__role'

    def sass_accredited_status(self, obj, **kwargs):
        text_only = kwargs.get('text_only', 'False')
        if text_only == 'True':
            false_response = 'False'
            true_response = 'True'
        else:
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

    def signed_up(self, obj, **kwargs):
        text_only = kwargs.get('text_only', 'False')
        if text_only == 'True':
            false_response = 'False'
            true_response = 'True'
        else:
            false_response = format_html(
                '<img src="/static/admin/img/icon-no.svg" alt="False">')
            true_response = format_html(
                '<img src="/static/admin/img/icon-yes.svg" alt="True">')
        if not obj.email:
            return false_response
        if obj.last_login:
            return true_response
        try:
            profile_data = json.loads(
                obj.bims_profile.data
            )
            if 'DateModified' in profile_data:
                return false_response
        except (ValueError, TypeError, BimsProfile.DoesNotExist):
            pass
        return true_response

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
            settings.DEFAULT_FROM_EMAIL,
            [obj.email],
            fail_silently=False
        )
        return super(CustomUserAdmin, self).response_add(
            request, obj, post_url_continue)

    def changelist_view(self, request, extra_context=None):
        test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
        if test[-1] and not test[-1].startswith('?'):
            if 'signed_up' not in request.GET:
                q = request.GET.copy()
                q['signed_up'] = 'True'
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)

class BaseMapLayerAdmin(OrderedModelAdmin):
    list_display = (
        'title',
        'url',
        'default_basemap',
        'move_up_down_links')
    list_filter = ('title',)
    ordering = ('order',)


class NonBiodiversityLayerAdmin(OrderedModelAdmin):
    list_display = (
        'order',
        'name',
        'wms_url',
        'wms_layer_name',
        'move_up_down_links',)
    list_filter = ('wms_url',)
    ordering = ('order',)


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

    def delete_model(self, request, obj):
        if obj.locked:
            self.message_user(
                request,
                "This record is locked and cannot be deleted.",
                level='warning')
        else:
            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.locked:
                self.message_user(
                    request,
                    f"Record with ID {obj.id} is locked and cannot be deleted.",
                    level='warning')
        queryset = queryset.filter(locked=False)
        if queryset:
            super().delete_queryset(request, queryset)


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
        'description',
        'display_order',
        'verified'
    )

    actions = ['merge_endemisms']

    def merge_endemisms(self, request, queryset):
        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 endemism', messages.ERROR
            )
            return
        if not verified.exists():
            self.message_user(
                request, 'Missing verified endemism', messages.ERROR)
            return
        if verified.count() > 1:
            self.message_user(
                request, 'There are more than 1 verified endemism',
                messages.ERROR)
            return
        excluded = verified[0]
        endemisms = queryset.exclude(id=verified[0].id)
        merge_endemism(excluded, endemisms)
        self.message_user(request, 'Endemism has been merged')

    merge_endemisms.short_description = 'Merge endemism'


class TaxonImagesInline(admin.TabularInline):
    model = TaxonImage
    raw_id_fields = (
        'survey',
        'owner',
        'uploader'
    )


class TaxonomyAdminForm(forms.ModelForm):
    class Meta:
        model = Taxonomy
        widgets = {
            'gbif_data': JSONEditorWidget
        }
        fields = '__all__'


class TaxonGroupTaxonomyInline(TabularInlinePaginated):
    model = TaxonGroupTaxonomy
    extra = 1
    raw_id_fields = ('taxonomy',)
    per_page = 20


class TaxonGroupAdmin(admin.ModelAdmin):
    inlines = [
        TaxonGroupTaxonomyInline,
    ]
    list_per_page = 20
    list_display = (
        'name',
        'singular_name',
        'category'
    )
    search_fields = (
        'name',
        'singular_name',
    )
    list_filter = (
        'category',
    )
    filter_horizontal = (
        'taxonomies',
        'experts'
    )
    raw_id_fields = (
        'gbif_parent_species',
    )


class TaxonGroupListFilter(django_admin.SimpleListFilter):
    title = 'Taxon Group'

    parameter_name = 'taxon_group'

    def lookups(self, request, model_admin):
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name)
        return [
            (taxon_group.id, taxon_group.name) for taxon_group in taxon_groups
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                taxongrouptaxonomy__taxongroup=self.value()
            )
        else:
            return queryset


class TaxonomyAdmin(admin.ModelAdmin):
    form = TaxonomyAdminForm
    change_form_template = 'admin/taxonomy_changeform.html'

    autocomplete_fields = (
        'vernacular_names',
    )

    list_display = (
        'canonical_name',
        'link_to_gbif',
        'scientific_name',
        'author',
        'rank',
        'parent',
        'import_date',
        'taxonomic_status',
        'accepted_taxonomy',
        'legacy_canonical_name',
        'iucn_status',
        'validated',
        'verified',
        'tag_list'
    )

    list_filter = (
        'rank',
        'verified',
        'import_date',
        'taxonomic_status',
        'iucn_status',
        TaxonGroupListFilter,
    )

    search_fields = (
        'scientific_name',
        'canonical_name',
        'legacy_canonical_name',
        'gbif_key',
    )

    raw_id_fields = (
        'parent',
        'accepted_taxonomy',
        'source_reference'
    )

    actions = [
        'merge_taxa', 'update_taxa', 'fetch_common_names', 'fetch_cites_listing', 'extract_author'
    ]

    def extract_author(self, request, queryset):
        author_year_pattern = re.compile(r'^(.*?)(\b\d{4}\b)')

        count_updated = 0
        for taxon in queryset:
            sci = taxon.scientific_name or ''
            canon = taxon.canonical_name or ''

            if canon and sci.startswith(canon):
                remainder = sci[len(canon):].strip()
                match = author_year_pattern.match(remainder)
                if match:
                    author_year = match.group(0).strip(", ")
                    taxon.author = author_year
                    taxon.save()
                    count_updated += 1

        self.message_user(
            request,
            f"Updated {count_updated} taxa with extracted author and year.")

    extract_author.short_description = "Extract author"

    inlines = [TaxonImagesInline]

    def fetch_cites_listing(self, request, queryset):
        taxa_ids = list(queryset.values_list('id', flat=True))
        chunk_size = 1000
        for chunk in chunk_list(taxa_ids, chunk_size):
            fetch_and_save_cites_listing.delay(chunk)
        self.message_user(request, "CITES data fetching initiated for selected taxa.")

    def fetch_common_names(self, request, queryset):
        taxa_ids = list(queryset.values_list('id', flat=True))
        fetch_vernacular_names.delay([str(taxa_id) for taxa_id in taxa_ids])

    def update_taxa(self, request, queryset):
        for taxa in queryset:
            if taxa.additional_data:
                taxa.additional_data['fetch_gbif'] = True
            else:
                taxa.additional_data = {
                    'fetch_gbif': True
                }
            taxa.save()

    def merge_taxa(self, request, queryset):
        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 taxon', messages.ERROR
            )
            return
        if not verified.exists():
            self.message_user(
                request, 'Missing verified taxon', messages.ERROR)
            return
        if verified.count() > 1:
            self.message_user(
                request, 'There are more than 1 verified taxon',
                messages.ERROR)
            return
        merge_taxa_data(
            excluded_taxon=verified[0],
            taxa_list=queryset.exclude(id=verified[0].id)
        )
        self.message_user(request, 'Taxa has been merged')

    merge_taxa.short_description = 'Merge taxa'

    def link_to_gbif(self, obj):
        if obj.gbif_key:
            link = 'https://gbif.org/species/{}'.format(obj.gbif_key)
            label = obj.gbif_key
            return format_html(
                '<a href="{}" target="_blank">{}</a>', link, label)
        else:
            return '-'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        scientific_name = Taxonomy.objects.get(pk=object_id).scientific_name

        if scientific_name is None:
            extra_context['results'] = None
            return super().change_view(
                request, object_id, form_url, extra_context=extra_context,
            )
        name = Taxonomy.objects.get(pk=object_id).scientific_name
        parameter = {'limit': 20, 'q': name}
        results = suggest_search(parameter)
        extra_context['results'] = json.dumps(results)
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


class VernacularNameAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
    )

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
    search_fields = ('uuid',)


class SassBiotopeAdmin(admin.ModelAdmin):

    def taxon_group_list(self, obj: Biotope):
        return [taxon_group.name for taxon_group in obj.taxon_group.all()]

    taxon_group_list.short_description = 'Taxon groups'

    def used_in_SASS(self, obj: Biotope):
        if obj.sassbiotopefraction_set.all().exists():
            return format_html(
                '<img src="/static/admin/img/icon-yes.svg" alt="True">')
        return format_html(
            '<img src="/static/admin/img/icon-no.svg" alt="False">')

    list_display = (
        'name',
        'display_order',
        'biotope_form',
        'biotope_type',
        'taxon_group_list',
        'used_in_SASS',
        'verified'
    )
    list_filter = (
        'name',
    )
    ordering = (
        'name',
        'display_order',
        'biotope_form'
    )

    actions = ['merge_biotopes']

    def merge_biotopes(self, request, queryset):
        from bims.models import merge_biotope
        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 biotope', messages.ERROR
            )
            return
        if not verified.exists():
            self.message_user(
                request, 'Missing verified biotope', messages.ERROR)
            return
        if verified.count() > 1:
            self.message_user(
                request, 'There are more than 1 verified biotope',
                messages.ERROR)
            return
        excluded = verified[0]
        biotopes = queryset.exclude(id=verified[0].id)
        merge_biotope(excluded, biotopes)
        self.message_user(request, 'Biotope has been merged')


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

    def taxon_group_list(self, obj: SamplingMethod):
        return [taxon_group.name for taxon_group in obj.taxon_group.all()]

    taxon_group_list.short_description = 'Taxon groups'

    list_display = (
        'sampling_method',
        'effort_measure',
        'verified',
        'taxon_group_list',
    )

    list_filter = (
        'sampling_method',
        'effort_measure',
        'verified'
    )

    actions = ['merge_sampling_methods']

    def merge_sampling_methods(self, request, queryset):
        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 sampling method', messages.ERROR
            )
            return
        if not verified.exists():
            self.message_user(
                request, 'Missing verified sampling method', messages.ERROR)
            return
        if verified.count() > 1:
            self.message_user(
                request, 'There are more than 1 verified sampling method',
                messages.ERROR)
            return
        excluded_sampling_method = verified[0]
        sampling_methods = queryset.exclude(id=verified[0].id)
        merge_sampling_method(
            excluded_sampling_method=excluded_sampling_method,
            sampling_methods=sampling_methods
        )
        self.message_user(request, 'Sampling method has been merged')

    merge_sampling_methods.short_description = 'Merge sampling methods'


class SiteImageAdmin(admin.ModelAdmin):
    list_display = (
        'get_site_code',
        'image',
        'date'
    )
    raw_id_fields = (
        'site',
        'site_visit',
        'survey'
    )
    search_fields = (
        'site__site_code',
        'site__legacy_site_code'
    )

    def get_site_code(self, obj):
        return obj.site.location_site_identifier

    get_site_code.short_description = 'Site'
    get_site_code.admin_order_field = 'site__site_code'


class BimsDocumentInline(admin.StackedInline):
    model = BimsDocument
    classes = ('collapse open',)
    inline_classes = ('collapse open',)


class BimsDocumentAdmin(DocumentAdmin):
    inlines = [BimsDocumentInline]


class ChemicalRecordAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = (
        'value',
        'chem',
        'date',
        'get_site_code'
    )
    raw_id_fields = (
        'location_site',
        'survey',
        'source_reference'
    )
    list_filter = (
        ('date', DateRangeFilter),
        'chem',
    )
    search_fields = (
        'location_site__site_code',
        'survey__site__site_code'
    )

    def get_site_code(self, obj):
        if obj.location_site:
            return obj.location_site.location_site_identifier
        elif obj.survey:
            return obj.survey.site.location_site_identifier
        return '-'

    get_site_code.short_description = 'Site Code'
    get_site_code.admin_order_field = 'site__site_code'


class ChemAdmin(admin.ModelAdmin):
    list_display = (
        'chem_code',
        'chem_description',
        'chem_unit',
        'show_in_abiotic_list',
        'minimum',
        'maximum'
    )
    list_filter = (
        'show_in_abiotic_list',
        'chem_unit'
    )
    search_fields = (
        'chem_code',
        'chem_description'
    )


class LocationContextFilterGroupOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'link_to_filter',
        'link_to_group',
        'filter_display_order',
        'group_display_order',
        'show_in_dashboard',
        'show_in_side_panel'
    )

    sortable_by = (
        'filter_display_order',
        'group_display_order',
    )

    def link_to_group(self, obj):
        link = reverse('admin:bims_locationcontextgroup_change',
                       args=[obj.group.id])
        return format_html(
            "<a href='#' onclick='showPopup(event, \"{}\" )'>{}</a>",
            link,
            obj.group.name,
        )

    def link_to_filter(self, obj):
        link = reverse('admin:bims_locationcontextfilter_change',
                       args=[obj.filter.id])
        return format_html(
            "<a href='#' onclick='showPopup(event, \"{}\" )'>{}</a>",
            link,
            obj.filter.title,
        )

    class Media:
        js = (
            'js/show_popup.js',
        )


class LocationContextFilterAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'display_order'
    )
    ordering = ('display_order',)


class SurveyAdmin(admin.ModelAdmin):

    date_hierarchy = 'date'
    raw_id_fields = (
        'site',
    )
    search_fields = (
        'site__site_code',
        'uuid'
    )
    list_filter = (
        ('date', DateRangeFilter),
    )
    list_display = (
        'id',
        'site',
        'date',
        'validated',
        'owner',
        'link_to_dashboard'
    )


    def link_to_dashboard(self, obj):
        link = reverse('site-visit-detail',
                       args=[obj.id])
        return format_html(
            "<a href='{}'>Dashboard ⎘</a>",
            link,
        )


class SurveyDataValueAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'survey',
    )
    list_display = (
        'survey',
        'survey_data',
        'survey_data_option'
    )


class AlgaeDataAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'survey',
    )
    list_display = (
        'survey',
        'curation_process',
        'indicator_chl_a',
        'indicator_afdm',
        'ai'
    )
    search_fields = (
        'survey__site__site_code',
    )
    list_filter = (
        'indicator_chl_a',
        'indicator_afdm',
    )


class DownloadRequestStatusFilter(django_admin.SimpleListFilter):
    title = _('Download Request Status')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('pending', _('Pending')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('processing', _('Processing')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'processing':
            return queryset.filter(
                processing=True
            ).exclude(
                Q(approved=True) | Q(rejected=True)
            )
        if self.value() == 'approved':
            return queryset.filter(
                approved=True
            )
        if self.value() == 'rejected':
            return queryset.filter(
                rejected=True
            )
        if self.value() == 'pending':
            return queryset.filter(
                Q(progress='') | Q(progress__isnull=True)
            )
        return queryset


class DownloadRequestAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'requester',
        'taxon',
        'survey',
        'location_site'
    )
    list_display = (
        'request_date',
        'requester',
        'resource_type',
        'resource_name',
        'purpose',
        'status'
    )
    list_filter = (
        DownloadRequestStatusFilter,
    )

    def status(self, obj: DownloadRequest):
        if obj.approved:
            return 'Approved'
        if obj.rejected:
            return 'Rejected'
        if obj.processing:
            return 'Processing'
        return 'Pending'


class DownloadRequestPurposeAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'name',
    )


class RequestLogAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'remote_address',
        'request_path',
        'response_status',
        'run_time'
    )


class IngestedDataAdmin(admin.ModelAdmin):
    list_display = (
        'datetime',
        'is_valid',
        'content_object',
        'get_content_object_id',
        'category',
        'data_key'
    )
    list_filter = (
        'is_valid',
        'category',
    )
    sortable_by = (
        'datetime',
        'is_valid',
        'category',
        'data_key'
    )
    search_fields = (
        'data_key',
    )

    def get_content_object_id(self, obj):
        return obj.content_object.id if obj.content_object else None

    get_content_object_id.short_description = 'Content Object ID'


class UploadSessionAdmin(admin.ModelAdmin):
    list_display = (
        'uploader',
        'module_group',
        'token',
        'uploaded_at',
        'category',
        'processed',
        'canceled'
    )


class LocationContextGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'key',
        'geocontext_group_key',
        'layer_name',
        'verified'
    )
    search_fields = (
        'name',
        'key',
        'geocontext_group_key'
    )
    actions = ['merge_group']

    def merge_group(self, request, queryset):
        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 group', messages.ERROR
            )
            return
        if not verified.exists():
            self.message_user(
                request, 'Missing verified group', messages.ERROR)
            return
        if verified.count() > 1:
            self.message_user(
                request, 'There are more than 1 verified group',
                messages.ERROR)
            return
        excluded_group = verified[0]
        group_list = queryset.exclude(id=verified[0].id)
        merge_context_group(
            excluded_group=excluded_group,
            group_list=group_list
        )
        self.message_user(request, 'Groups has been merged')

    merge_group.short_description = 'Merge groups'


class WaterTemperatureAdmin(admin.ModelAdmin):
    list_display = (
        'value', 'date_time', 'is_daily', 'maximum', 'minimum'
    )
    raw_id_fields = (
        'location_site', 'uploader', 'owner', 'source_reference'
    )
    search_fields = (
        'location_site__site_code',
    )
    list_filter = (
        'date_time',
    )


class WaterTemperatureThresholdAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'location_site', 'creator'
    )
    raw_id_fields = (
        'location_site', 'creator'
    )


class TaxonExtraAttributeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'taxon_group'
    )


class DecisionSupportToolNameAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


class DecisionSupportToolAdmin(admin.ModelAdmin):
    change_list_template = 'admin/dst_changelist.html'
    list_display = (
        'dst_name',
        'get_bio_uuid'
    )
    raw_id_fields = (
        'biological_collection_record',
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'dst_name__name',
        'biological_collection_record__uuid'
    )

    def get_bio_uuid(self, obj):
        if obj.biological_collection_record:
            return obj.biological_collection_record.uuid
        return '-'

    get_bio_uuid.short_description = 'Biological Collection Record UUID'
    get_bio_uuid.admin_order_field = 'biological_collection_record__uuid'


class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_name', 'unit',)
    list_filter = ('unit_name', 'unit',)
    search_fields = ('unit_name', 'unit',)


class ClimateDataAdmin(admin.ModelAdmin):
    list_display = ('title', 'climate_geocontext_group_key')


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'get_users', 'site')

    def get_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])
    get_users.short_description = 'Users'

    filter_horizontal = ('users',)


class TaxonImageAdmin(admin.ModelAdmin):
    list_display = ('taxonomy', 'source', 'date')
    raw_id_fields = ('taxonomy', 'uploader', 'owner', 'survey')


class RecordTypeAdmin(OrderedModelAdmin):
    list_display = (
        'name',
        'verified',
        'total_records',
        'is_hidden_in_form',
        'move_up_down_links',
        'order',)
    ordering = ('order',)

    def total_records(self, obj):
        return BiologicalCollectionRecord.objects.filter(
            record_type=obj
        ).count()

    total_records.short_description = 'Total Occurrences'

    actions = ['merge_record_types']

    def merge_record_types(self, request, queryset):
        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 record type', messages.ERROR
            )
            return
        if not verified.exists():
            self.message_user(
                request, 'Missing verified record type', messages.ERROR)
            return
        merge_record_types(
            primary_record_type=verified.first(),
            record_type_list=queryset
        )


    merge_record_types.short_description = 'Merge record types'


class WetlandIndicatorStatusAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links', 'order')
    ordering = ('order',)


class HydroperiodAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links', 'order')
    ordering = ('order',)


class AbundanceTypeAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links', 'order')
    ordering = ('order',)


class SamplingEffortMeasureAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links', 'order')
    ordering = ('order',)


class HarvestSessionAdmin(admin.ModelAdmin):
    list_display = (
        'start_time', 'status', 'harvester',
        'module_group',
        'finished', 'canceled', 'is_fetching_species')

    actions = [
        'resume_harvest',
    ]

    def resume_harvest(self, request, queryset):
        from bims.tasks.harvest_collections import (
            harvest_collections
        )
        if len(queryset) > 1:
            message = 'You can only resume one session'
            self.message_user(request, message, level=messages.ERROR)
            return

        queryset.first().canceled = False
        queryset.first().save()

        full_message = 'Resumed'
        harvest_collections.delay(
            queryset.first().id,
            True
        )

        self.message_user(request, full_message)


class TaxonGroupTaxonomyAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'taxonomy',
    )
    list_display = (
        'taxongroup',
        'taxonomy',
        'is_validated'
    )
    search_fields = ('taxonomy__scientific_name', 'taxonomy__canonical_name')
    actions = ('create_proposal', )

    def create_proposal(self, request, queryset):
        """Action to create proposal"""
        unvalidated = queryset.filter(is_validated=False, is_rejected=False)
        for data in unvalidated:
            create_taxon_proposal(data.taxonomy, data.taxongroup)

        self.message_user(
            request,
            'Proposal has been created for {} data'.format(
                unvalidated.count()))


class TaxonomyUpdateProposalAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'original_taxonomy',
        'accepted_taxonomy',
        'parent',
        'owner',
        'collector_user',
        'analyst'
    )
    list_display = (
        'original_taxonomy',
        'scientific_name',
        'canonical_name',
        'status',
        'created_at'
    )
    autocomplete_fields = (
        'vernacular_names',
    )


class TaxonomyUpdateReviewerAdmin(admin.ModelAdmin):
    list_display = (
        'taxonomy_update_proposal',
        'reviewer',
        'status'
    )


@admin.register(CITESListingInfo)
class CITESListingInfoAdmin(admin.ModelAdmin):
    list_display = ('appendix', 'effective_at', 'taxonomy')
    list_filter = ('appendix', 'effective_at')
    search_fields = ('annotation', 'taxonomy__name')
    raw_id_fields = ('taxonomy',)


class RoleAdminForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['display_name']


@admin.register(Role)
class RoleAdmin(OrderedModelAdmin):
    list_display = ('display_name', 'move_up_down_links')
    ordering = ('order',)
    form = RoleAdminForm


@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('celery_task_id', 'in_progress', 'created_at', 'updated_at')
    list_filter = ('in_progress', 'created_at', 'updated_at')
    search_fields = ('celery_task_id',)


class FlatPageExtensionInline(admin.StackedInline):
    model = FlatPageExtension
    can_delete = False
    verbose_name_plural = 'Custom Options'
    fk_name = 'flatpage'


class ExtendedFlatPageAdmin(FlatPageAdmin):
    inlines = (FlatPageExtensionInline,)

    fieldsets = (
        (None, {
            "fields": ("url", "title", "content"),
        }),
        ("Advanced options", {
            "classes": ("collapse",),
            "fields": ("registration_required", "template_name"),
        }),
    )

    formfield_overrides = {
        models.TextField: {
            'widget': CKEditorUploadingWidget}
    }

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.sites.set(Site.objects.all())

    def show_in_navbar(self, instance):
        return instance.extension.show_in_navbar
    show_in_navbar.short_description = "Show in Navbar"
    show_in_navbar.boolean = True

    def display_order(self, instance):
        return instance.extension.display_order
    display_order.short_description = "Display Order"

    list_display = ('title', 'url', 'show_in_navbar', 'display_order')


class DatasetAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'abbreviation')
    search_fields = ('uuid', 'name')
    change_list_template = "admin/dataset_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch-datasets/', self.fetch_datasets, name='fetch_datasets'),
        ]
        return custom_urls + urls

    def fetch_datasets(self, request):
        from bims.tasks.dataset import retrieve_datasets_from_gbif
        retrieve_datasets_from_gbif.delay()
        self.message_user(request, 'Fetching datasets in background')
        return HttpResponseRedirect(reverse('admin:bims_dataset_changelist'))

class TagGroupAdmin(OrderedModelAdmin):
    ordering = ('order',)
    list_display = ('id', 'move_up_down_links', 'name', 'colour')


# Re-register GeoNode's Profile page
admin.site.unregister(Profile)
admin.site.register(Profile, CustomUserAdmin)

admin.site.register(LocationSite, LocationSiteAdmin)
admin.site.register(LocationType)
admin.site.register(IUCNStatus, IUCNStatusAdmin)
admin.site.register(Endemism, EndemismAdmin)
admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveyData)
admin.site.register(SurveyDataOption)
admin.site.register(SurveyDataValue, SurveyDataValueAdmin)
admin.site.register(NonBiodiversityLayer, NonBiodiversityLayerAdmin)
admin.site.register(Taxonomy, TaxonomyAdmin)
admin.site.register(TaxonGroup, TaxonGroupAdmin)

admin.site.register(Boundary, BoundaryAdmin)
admin.site.register(BoundaryType, admin.ModelAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(BiologicalCollectionRecord, BiologicalCollectionAdmin)

admin.site.register(ShapefileUploadSession, ShapefileUploadSessionAdmin)
admin.site.register(Shapefile, ShapefileAdmin)

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
admin.site.register(SiteSetting, SiteSettingAdmin)
admin.site.register(GeocontextSetting, PreferencesAdmin)
admin.site.register(ChemicalRecord, ChemicalRecordAdmin)
admin.site.register(Chem, ChemAdmin)
admin.site.register(UploadSession, UploadSessionAdmin)
admin.site.register(HarvestSession, HarvestSessionAdmin)
admin.site.register(DashboardConfiguration)
admin.site.register(DownloadRequest, DownloadRequestAdmin)
admin.site.register(DownloadRequestPurpose, DownloadRequestPurposeAdmin)
admin.site.register(BaseMapLayer, BaseMapLayerAdmin)
admin.site.register(RequestLog, RequestLogAdmin)
admin.site.register(IngestedData, IngestedDataAdmin)

admin.site.register(TaxonImage, TaxonImageAdmin)

admin.site.register(LocationContextGroup, LocationContextGroupAdmin)
admin.site.register(
    LocationContextFilterGroupOrder, LocationContextFilterGroupOrderAdmin)
admin.site.register(LocationContextFilter, LocationContextFilterAdmin)

# Hide upload files from geonode in admin
# admin.site.unregister(Upload)
# admin.site.unregister(UploadFile)

# Rerender geonode document admin
admin.site.unregister(Document)
admin.site.register(Document, BimsDocumentAdmin)

admin.site.register(AlgaeData, AlgaeDataAdmin)

if TRACK_PAGEVIEWS:
    admin.site.register(Pageview, PageviewAdmin)

from bims.custom_admin import *  # noqa

admin.site.register(WaterTemperature, WaterTemperatureAdmin)
admin.site.register(TaxonExtraAttribute, TaxonExtraAttributeAdmin)
admin.site.register(DecisionSupportTool, DecisionSupportToolAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(ClimateData, ClimateDataAdmin)
admin.site.register(BimsProfile, BimsProfileAdmin)
admin.site.register(
    DecisionSupportToolName, DecisionSupportToolNameAdmin)
admin.site.register(
    WaterTemperatureThreshold, WaterTemperatureThresholdAdmin
)
admin.site.register(
    Notification,
    NotificationAdmin
)
admin.site.register(RecordType, RecordTypeAdmin)
admin.site.register(
    WetlandIndicatorStatus, WetlandIndicatorStatusAdmin)
admin.site.register(
    Hydroperiod,
    HydroperiodAdmin
)
admin.site.register(
    AbundanceType,
    AbundanceTypeAdmin,
)
admin.site.register(
    SamplingEffortMeasure,
    SamplingEffortMeasureAdmin
)
admin.site.register(
    TaxonGroupTaxonomy,
    TaxonGroupTaxonomyAdmin
)
admin.site.register(
    TaxonomyUpdateProposal,
    TaxonomyUpdateProposalAdmin
)
admin.site.register(
    TaxonomyUpdateReviewer,
    TaxonomyUpdateReviewerAdmin
)
admin.site.register(
    Invasion,
    InvasionAdmin
)

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, ExtendedFlatPageAdmin)
admin.site.register(TagGroup, TagGroupAdmin)
admin.site.register(Dataset, DatasetAdmin)
