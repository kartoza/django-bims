import base64
import datetime

from sass.models.rate import Rate

from sass.models.sass_biotope_fraction import SassBiotopeFraction

from bims.models.site_image import SiteImage, COLLECTION_RECORD_KEY

from sass.models.site_visit_taxon import SiteVisitTaxon

from sass.models.site_visit_biotope_taxon import SiteVisitBiotopeTaxon

from bims.models.biotope import Biotope
from django.db.models import Q
from rest_framework.response import Response
from sass.models.taxon_abundance import TaxonAbundance

from sass.models.sass_taxon import SassTaxon

from sass.models.site_visit import SiteVisit

from bims.models.location_site import LocationSite
from django.core.files.base import ContentFile
from rest_framework.views import APIView

from sass.views.sass_form import SassFormView

BIOTOPE_TYPES = {
    'sic': 'Stones in current',
    'sooc': 'Stones out of current',
    'be': 'Bedrock',
    'ave': 'Aquatic vegetation',
    'mvic': 'Marginal vegetation in current',
    'mvoc': 'Marginal vegetation out of current',
    'gr': 'Gravel',
    'sa': 'Sand',
    'smc': 'Silt/mud/clay',
}


class AddSASS(APIView):

    def post(self, request, *args, **kwargs):
        """
        Add sass data from mobile
        :param request: {
            'data': {
                'siteImage': '',
                'siteId': '',
                'date': '2022-11-24T01:36:42.543Z',
                'otherBiota': '',
                'comments': '',
                'sassTaxa': {
                    '{SassTaxaGroup}': {
                        '{SassTaxon}': {
                            'stones': 'A',
                            'site': 'A
                        }
                    }
                },
                'biotope': {
                    'sooc': 1 ,
                    ...
                }
            }
        }
        :param args:
        :param kwargs:
        :return:
        """
        post_data = request.data

        site = LocationSite.objects.get(
            id=post_data.get('siteId', '')
        )
        date = datetime.datetime.strptime(
            post_data.get('date'),
            '%Y-%m-%dT%H:%M:%S.%fZ')

        # Create a site visit
        site_visit = SiteVisit.objects.create(
            location_site=site,
            site_visit_date=date,
            time=date,
            sass_version=5,
            owner=self.request.user,
            collector=self.request.user
        )

        survey = SassFormView.create_or_get_survey(site_visit)

        site_image_str = post_data.get('siteImage', '')
        site_image = None
        if site_image_str:
            site_image_name = (
                f'{post_data["date"]}_{request.user.id}_'
                f'sass_site_image_mobile.jpeg'
            )
            site_image = ContentFile(
                base64.b64decode(site_image_str), name=site_image_name)

        if site_image:
            SiteImage.objects.get_or_create(
                site=site,
                image=site_image,
                date=date,
                form_uploader=COLLECTION_RECORD_KEY,
                survey=survey,
                site_visit=site_visit
            )

        # Process Biotope sampled data
        biotope_sampled = post_data.get('biotope', {})
        biotope_fractions = []
        for biotope_key, biotope_value in biotope_sampled.items():
            biotope_label = BIOTOPE_TYPES[biotope_key]
            if biotope_label == 'Sand':
                biotope = Biotope.objects.filter(
                    name__iexact=biotope_label,
                    sassbiotopefraction__isnull=False
                ).distinct().first()
            else:
                biotope = Biotope.objects.filter(
                    name__icontains=biotope_label,
                    sassbiotopefraction__isnull=False
                ).distinct().first()

            rate = Rate.objects.filter(
                rate=biotope_value,
                group=2
            ).exclude(description__icontains='not rated').first()
            biotope_fraction, created = (
                SassBiotopeFraction.objects.get_or_create(
                    rate=rate,
                    sass_biotope_id=biotope.id
                )
            )
            biotope_fractions.append(biotope_fraction)
        if len(biotope_fractions) > 0:
            site_visit.sass_biotope_fraction.add(*biotope_fractions)

        # Process Sass Taxa data
        sass_taxa = post_data.get('sassTaxa', {})
        biotope_labels = {
            'stones': 'SIC/SOOC',
            'vegetation': 'MV/AQV',
            'gravel_sand_mud': 'G/S/M'
        }
        for sass_taxa_group in sass_taxa:
            for taxon_name, taxon_biotope in sass_taxa[sass_taxa_group].items():
                sass_taxon = SassTaxon.objects.filter(
                    Q(taxon_sass_4=taxon_name) |
                    Q(taxon_sass_5=taxon_name)
                ).first()
                for biotope_label in biotope_labels:
                    if (
                        biotope_label in taxon_biotope
                            and taxon_biotope[biotope_label]
                    ):
                        taxon_abundance = TaxonAbundance.objects.get(
                            abc=taxon_biotope[biotope_label]
                        )
                        biotope = Biotope.objects.get(
                            name=biotope_labels[biotope_label]
                        )
                        SiteVisitBiotopeTaxon.objects.get_or_create(
                            site_visit=site_visit,
                            sass_taxon=sass_taxon,
                            taxon=sass_taxon.taxon,
                            biotope=biotope,
                            taxon_abundance=taxon_abundance,
                            date=date
                        )
                if 'site' in taxon_biotope and taxon_biotope['site']:
                    taxon_abundance = TaxonAbundance.objects.get(
                        abc=taxon_biotope['site']
                    )
                    site_visit_taxon, created = (
                        SiteVisitTaxon.objects.get_or_create(
                            site=site_visit.location_site,
                            site_visit=site_visit,
                            sass_taxon=sass_taxon,
                            taxonomy=sass_taxon.taxon,
                            original_species_name=
                            sass_taxon.taxon.canonical_name,
                            validated=False,
                            survey=survey
                        )
                    )
                    site_visit_taxon.notes = 'from sass'
                    site_visit_taxon.collection_date = date
                    site_visit_taxon.taxon_abundance = taxon_abundance
                    site_visit_taxon.collector_user = site_visit.collector
                    site_visit_taxon.save()

        return Response({
            'survey_id': survey.id,
            'id': site_visit.id,
        })
