from sass.views.sass_form import *
from sass.models.sass_taxon import SassTaxon
from sass.models.taxon_abundance import TaxonAbundance


site_visits = SiteVisit.objects.filter(
    sitevisitbiotopetaxon__isnull=False,
    sitevisittaxon__isnull=True
)

print('Updating {}'.format(site_visits.count()))

for site_visit in site_visits:
    print('Fixing site visit {}'.format(site_visit.id))
    biotope_taxa = site_visit.sitevisitbiotopetaxon_set.all()
    sass_taxa = SassTaxon.objects.filter(
        id__in=biotope_taxa.distinct('sass_taxon').values('sass_taxon')
    )
    for taxon in sass_taxa:
        print('Taxonomy {}'.format(taxon.taxon.canonical_name))
        _biotope_taxa = biotope_taxa.filter(
            sass_taxon=taxon
        )
        abundances = []
        for __biotope_taxon in _biotope_taxa:
            abundances.append(__biotope_taxon.taxon_abundance.abc)
        greatest = get_greatest_sass_scores(abundances)
        taxon_abundance = TaxonAbundance.objects.get(
            abc=greatest
        )
        print('greatest : {}'.format(taxon_abundance.abc))
        svt, created = SiteVisitTaxon.objects.get_or_create(
            site_visit=site_visit,
            sass_taxon=taxon,
            taxon_abundance=taxon_abundance,
            taxonomy=taxon.taxon,
            site=site_visit.location_site
        )
        print('Created : {}'.format(created))

    print('---------------------------------')

