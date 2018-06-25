# coding=utf-8
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.gis import admin
from django.core.mail import send_mail
from django.shortcuts import redirect
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
    CarouselHeader,
    BiologicalCollectionRecord,
    Category,
    Link,
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


class BiologicalCollectionAdmin(admin.ModelAdmin):
    list_display = (
        'original_species_name',
        'category',
        'collection_date',
        'validated',
    )


class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


admin.site.register(Category)
admin.site.register(Link, LinkAdmin)


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


class CustomUserAdmin(UserAdmin):
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
        return redirect('/admin/auth/user/')


    # Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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
