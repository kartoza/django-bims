# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from biobase.models.bio_taxon import BioTaxon


class BioTaxonAdmin(admin.ModelAdmin):
    list_display = (
        'bio_taxon_name',
        'taxonomy',
        'note',
    )


admin.site.register(BioTaxon, BioTaxonAdmin)
