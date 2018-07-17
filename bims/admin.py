# coding=utf-8
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis import admin
from django.core.mail import send_mail
from geonode.people.admin import ProfileAdmin
from geonode.people.forms import ProfileCreationForm
from geonode.people.models import Profile
from ordered_model.admin import OrderedModelAdmin

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
    CarouselHeader,
    BiologicalCollectionRecord,
    Category,
    Link,
    Author,
    Editor,
    Journal,
    Publisher,
    Entry,
    Collection,
    AuthorEntryRank,
    ShapefileUploadSession,
    Shapefile
)


class AuthorEntryRankInline(admin.TabularInline):
    extra = 1
    model = AuthorEntryRank
    ordering = ('rank',)


class AbstractHumanAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
    ordering = ('last_name', 'first_name')


class AuthorAdmin(AbstractHumanAdmin):
    list_display = ('last_name', 'first_name', 'user')
    raw_id_fields = ('user',)


class EditorAdmin(AbstractHumanAdmin):
    raw_id_fields = ('user',)


class AbstractEntityAdmin(admin.ModelAdmin):
    ordering = ('name',)


class JournalAdmin(AbstractEntityAdmin):
    pass


class PublisherAdmin(AbstractEntityAdmin):
    pass


class EntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'publication_date'
    fieldsets = (
        ('Publication core fields', {
            'fields': ('type', 'title', 'journal',
                       ('volume', 'number'),
                       ('pages',),
                       ('publication_date',
                        'is_partial_publication_date'),
                       'url')
        }),
        ('Identifiers', {
            'fields': (('doi', 'issn'), ('isbn', 'pmid'))
        }),
        ('Book fields', {
            'fields': ('booktitle', 'edition', 'chapter')
        }),
        ('PhD Thesis', {
            'fields': ('school',)
        }),
        ('Proceedings', {
            'fields': ('organization',)
        }),
        ('Miscellaneous', {
            'fields': ('editors', 'publisher', 'address', 'annote', 'note')
        }),
        ('Cross References', {
            'fields': ('crossref',)
        }),
    )
    inlines = (AuthorEntryRankInline,)
    list_display = ('title', 'first_author', 'type', 'publication_date',
                    'journal')
    list_filter = ('publication_date', 'journal', 'authors')
    list_per_page = 20
    list_select_related = True
    ordering = ('-publication_date',)
    raw_id_fields = ('authors', 'crossref')
    search_fields = ('title',)


class CollectionAdmin(admin.ModelAdmin):
    def size(self, obj):
        """Get the number of entries in each collection"""
        return obj.entries.count()

    list_display = ('name', 'size')
    raw_id_fields = ('entries',)


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
        'owner',
    )

class ShapefileInline(admin.TabularInline):

    def shapefile_name(self, obj):
        if obj.shapefile:
            return mark_safe("""<a href="%s" />%s</a>""" % (obj.shapefile.fileurl, obj.shapefile.filename))

    model = ShapefileUploadSession.shapefiles.through
    fields = ('shapefile_name', 'shapefile')
    readonly_fields = ('shapefile_name',)


class ShapefileUploadSessionAdmin(admin.ModelAdmin):
    exclude = ('shapefiles',)
    list_display = (
        'uploader',
        'uploaded_at',
        'processed',
    )

    inlines = (ShapefileInline,)


class ShapefileAdmin(admin.ModelAdmin):
    list_display = (
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


# Re-register GeoNode's Profile page
admin.site.unregister(Profile)
admin.site.register(Profile, CustomUserAdmin)

# register bibliography models
admin.site.register(Author, AuthorAdmin)
admin.site.register(Editor, EditorAdmin)
admin.site.register(Journal, JournalAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Collection, CollectionAdmin)

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
admin.site.register(BiologicalCollectionRecord, BiologicalCollectionAdmin)

admin.site.register(ShapefileUploadSession, ShapefileUploadSessionAdmin)
admin.site.register(Shapefile, ShapefileAdmin)
