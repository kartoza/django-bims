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
    SassEcologicalCategory,
    SassEcologicalCondition,
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


class SassEcologicalCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'category',
        'name',
        'colour'
    )

    ordering = ('order', )


class SassEcologicalConditionAdmin(admin.ModelAdmin):
    list_display = (
        'ecoregion_level_1',
        'geomorphological_zone',
        'ecological_category',
        'sass_score_precentile',
        'aspt_score_precentile'
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
admin.site.register(SassEcologicalCategory, SassEcologicalCategoryAdmin)
admin.site.register(SassEcologicalCondition, SassEcologicalConditionAdmin)
