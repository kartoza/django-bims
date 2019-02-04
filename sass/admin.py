# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django_extensions.admin import ForeignKeyAutocompleteAdmin
from sass.models import (
    River,
    SiteVisit,
    SassBiotopeFraction,
    Rate,
    SassTaxon,
    SiteVisitBiotopeTaxon,
    TaxonAbundance,
    SassValidationStatus,
    SiteVisitTaxon,
    Chem,
    SiteVisitChem,
    SASS5Sheet,
    SASS5Record,
    SamplingMethod,
)


class RiverAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'validated')
    list_filter = ('owner',)
    ordering = ('name', 'owner', 'validated')


class SiteVisitAdmin(ForeignKeyAutocompleteAdmin):
    list_display = (
        'location_site',
        'assessor',
        'site_visit_date',
        'water_level',
        'water_turbidity',
        'canopy_cover'
    )
    list_filter = (
        'water_level',
        'water_turbidity',
        'canopy_cover'
    )
    raw_id_fields = (
        'location_site',
    )


class RateAdmin(admin.ModelAdmin):
    list_display = (
        'rate',
        'description',
        'group'
    )


class SassBiotopeFractionAdmin(admin.ModelAdmin):
    list_display = (
        'rate',
        'sass_biotope'
    )
    list_filter = (
        'rate',
        'sass_biotope'
    )


class SassTaxonAdmin(admin.ModelAdmin):
    list_display = (
        'taxon',
        'score'
    )


class TaxonAbundanceAdmin(admin.ModelAdmin):
    list_display = (
        'abc',
        'description',
        'display_order'
    )


class SiteVisitBiotopeTaxonAdmin(admin.ModelAdmin):
    list_display = (
        'site_visit',
        'taxon',
        'biotope',
        'taxon_abundance'
    )

    list_filter = (
        'taxon',
        'taxon_abundance'
    )

    raw_id_fields = (
        'site_visit',
        'taxon'
    )


class SassValidationStatusAdmin(admin.ModelAdmin):
    list_display = (
        'status',
        'colour',
    )


class SiteVisitTaxonAdmin(admin.ModelAdmin):
    list_display = (
        'site_visit',
        'taxonomy',
        'taxon_abundance'
    )

    raw_id_fields = (
        'site_visit',
        'site',
        'taxonomy'
    )


class ChemAdmin(admin.ModelAdmin):
    list_display = (
        'chem_code',
        'chem_description',
        'chem_unit',
    )


class SiteVisitChemAdmin(admin.ModelAdmin):
    list_display = (
        'site_visit',
        'chem',
        'chem_value',
    )

    list_filter = (
        'chem',
    )

    raw_id_fields = (
        'site_visit',
    )


class SASS5SheetAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'rhp_site_code',
        'location_site'
    )

    raw_id_fields = (
        'location_site',
    )


class SASS5RecordAdmin(admin.ModelAdmin):
    list_display = (
        'sass_sheet',
        'taxonomy',
        'count'
    )

    raw_id_fields = (
        'sass_sheet',
    )


class SamplingMethodAdmin(admin.ModelAdmin):
    list_display = (
        'sampling_method',
        'effort_measure'
    )


# Register your models here.
admin.site.register(River, RiverAdmin)
admin.site.register(SiteVisit, SiteVisitAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(SassBiotopeFraction, SassBiotopeFractionAdmin)
admin.site.register(SassTaxon, SassTaxonAdmin)
admin.site.register(TaxonAbundance, TaxonAbundanceAdmin)
admin.site.register(SiteVisitBiotopeTaxon, SiteVisitBiotopeTaxonAdmin)
admin.site.register(SassValidationStatus, SassValidationStatusAdmin)
admin.site.register(SiteVisitTaxon, SiteVisitTaxonAdmin)
admin.site.register(Chem, ChemAdmin)
admin.site.register(SiteVisitChem, SiteVisitChemAdmin)
admin.site.register(SASS5Sheet, SASS5SheetAdmin)
admin.site.register(SASS5Record, SASS5RecordAdmin)
admin.site.register(SamplingMethod, SamplingMethodAdmin)
