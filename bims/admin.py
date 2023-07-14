# coding=utf-8
import csv
from datetime import timedelta
from datetime import date
import json

from django.http import HttpResponse
from rangefilter.filter import DateRangeFilter
from preferences.admin import PreferencesAdmin
from preferences import preferences

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
from django.db.models import Q
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, \
    ReadOnlyPasswordHashField

from django_json_widget.widgets import JSONEditorWidget

from bims.tasks import fetch_vernacular_names
from bims.utils.endemism import merge_endemism
from bims.utils.sampling_method import merge_sampling_method
from geonode.documents.admin import DocumentAdmin
from geonode.documents.models import Document
from geonode.people.admin import ProfileAdmin
from geonode.people.models import Profile
from ordered_model.admin import OrderedModelAdmin

from ckeditor.widgets import CKEditorWidget

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
    WaterTemperatureThreshold
)
from bims.models.climate_data import ClimateData
from bims.utils.fetch_gbif import merge_taxa_data
from bims.conf import TRACK_PAGEVIEWS
from bims.models.profile import Profile as BimsProfile
from bims.utils.gbif import search_exact_match, get_species, suggest_search
from bims.utils.location_context import merge_context_group
from bims.utils.user import merge_users
from bims.tasks.location_site import (
    update_location_context as update_location_context_task,
    update_site_code as update_site_code_task
)


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


class LocationSiteAdmin(admin.GeoModelAdmin):
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
    list_filter = (HasLocationContextDocument,)
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
        site_setting_group_keys = (
            preferences.GeocontextSetting.geocontext_keys.split(',')
        )
        groups = LocationContext.objects.filter(
            site=obj,
            group__geocontext_group_key__in=site_setting_group_keys
        ).values(
            'group__geocontext_group_key'
        ).distinct('group__geocontext_group_key')
        percentage = 0
        if groups.count() > 0:
            percentage = round(
                groups.count() / len(site_setting_group_keys) * 100
            )
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
                location_site.id, False, generate_spatial_scale_filter)
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


class IUCNStatusAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'sensitive',
                    'iucn_colour', 'national', 'total_species')

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
        'taxonomy',
        'taxonomy__origin',
        'record_type',
        'sampling_method'
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
            return '-'

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
        'role',
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
            obj.email,
            [obj.email],
            fail_silently=False
        )
        return super(CustomUserAdmin, self).response_add(
            request, obj, post_url_continue)


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


class TaxonomyAdminForm(forms.ModelForm):
    class Meta:
        model = Taxonomy
        widgets = {
            'gbif_data': JSONEditorWidget
        }
        fields = '__all__'


class TaxonGroupAdmin(admin.ModelAdmin):
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
        'rank',
        'parent',
        'import_date',
        'taxonomic_status',
        'legacy_canonical_name',
        'iucn_status',
        'validated',
        'verified'
    )

    list_filter = (
        'rank',
        'verified',
        'import_date',
        'taxonomic_status',
        'iucn_status'
    )

    search_fields = (
        'scientific_name',
        'canonical_name',
        'legacy_canonical_name',
    )

    raw_id_fields = (
        'parent',
        'accepted_taxonomy'
    )

    actions = ['merge_taxa', 'update_taxa', 'fetch_common_names']

    inlines = [TaxonImagesInline]

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
admin.site.register(GeocontextSetting, PreferencesAdmin)
admin.site.register(ChemicalRecord, ChemicalRecordAdmin)
admin.site.register(Chem, ChemAdmin)
admin.site.register(UploadSession, UploadSessionAdmin)
admin.site.register(HarvestSession)
admin.site.register(DashboardConfiguration)
admin.site.register(DownloadRequest, DownloadRequestAdmin)
admin.site.register(DownloadRequestPurpose, DownloadRequestPurposeAdmin)
admin.site.register(BaseMapLayer, BaseMapLayerAdmin)
admin.site.register(RequestLog, RequestLogAdmin)
admin.site.register(IngestedData, IngestedDataAdmin)

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
