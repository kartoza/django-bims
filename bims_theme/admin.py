# coding=utf-8

from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from bims_theme.models import (
    CustomTheme,
    CarouselHeader
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


admin.site.register(CustomTheme, CustomThemeAdmin)
admin.site.register(CarouselHeader, CarouselHeaderAdmin)
