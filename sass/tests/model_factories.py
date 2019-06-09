import factory

from django.utils import timezone

from sass.models import (
    SiteVisit,
    SiteVisitTaxon,
    SiteVisitBiotopeTaxon,
    SassTaxon,
    TaxonAbundance
)
from bims.tests.model_factories import (
    LocationSiteF,
    UserF,
    TaxonomyF,
    BiotopeF
)


class TaxonAbundanceF(factory.django.DjangoModelFactory):
    class Meta:
        model = TaxonAbundance


class SassTaxonF(factory.django.DjangoModelFactory):
    class Meta:
        model = SassTaxon


class SiteVisitF(factory.django.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('id',)
        model = SiteVisit

    id = factory.Sequence(lambda n: n)
    location_site = factory.SubFactory(LocationSiteF)
    site_visit_date = timezone.now()
    owner = factory.SubFactory(UserF)
    sass_version = 5


class SiteVisitBiotopeTaxonF(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteVisitBiotopeTaxon

    site_visit = factory.SubFactory(SiteVisitF)
    taxon = factory.SubFactory(TaxonomyF)
    sass_taxon = factory.SubFactory(SassTaxonF)
    biotope = factory.SubFactory(BiotopeF)
    taxon_abundance = factory.SubFactory(TaxonAbundanceF)
    date = timezone.now()


class SiteVisitTaxonF(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteVisitTaxon
