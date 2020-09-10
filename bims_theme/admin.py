# coding=utf-8

from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from bims_theme.models import (
    CustomTheme,
    CarouselHeader,
    Partner,
    LandingPageSection,
    LandingPageSectionContent
)


class CustomThemeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'date',
        'is_enabled'
    )


class CarouselHeaderAdmin(OrderedModelAdmin):
    list_display = ('order', 'description', 'banner', 'move_up_down_links')


class PartnerAdmin(OrderedModelAdmin):
    list_display = ('order', 'name', 'link', 'move_up_down_links')


class LandingPageSectionAdmin(OrderedModelAdmin):
    list_display = ('name', 'title', 'move_up_down_links')


class LandingPageSectionContentAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links')


admin.site.register(CustomTheme, CustomThemeAdmin)
admin.site.register(CarouselHeader, CarouselHeaderAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(LandingPageSection, LandingPageSectionAdmin)
admin.site.register(LandingPageSectionContent, LandingPageSectionContentAdmin)
