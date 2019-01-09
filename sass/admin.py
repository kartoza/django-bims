# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from sass.models import (
    River,
    SiteVisit
)


class RiverAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'validated')
    list_filter = ('owner',)
    ordering = ('name', 'owner', 'validated')


class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('assessor', 'site_visit_date')


# Register your models here.
admin.site.register(River, RiverAdmin)
admin.site.register(SiteVisit, SiteVisitAdmin)
