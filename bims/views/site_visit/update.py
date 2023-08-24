import time
import uuid
from datetime import datetime as libdatetime

from django.contrib.auth import get_user_model

from bims.models.taxonomy import Taxonomy
from django.views.generic.edit import UpdateView
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from bims.models.survey import Survey
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.views.mixin.session_form.mixin import SessionFormMixin
from bims.models.site_image import SiteImage
from bims.views.site_visit.base import SiteVisitBaseView
from bims.models.algae_data import AlgaeData
from bims.models.chem import Chem
from bims.models.chemical_record import ChemicalRecord


class SiteVisitUpdateView(
    UserPassesTestMixin,
    SiteVisitBaseView,
    UpdateView,
    SessionFormMixin):
    template_name = 'site_visit/site_visit_update.html'
    pk_url_kwarg = 'sitevisitid'
    model = Survey
    fields = ['site', 'date']
    collection_records = BiologicalCollectionRecord.objects.none()
    session_identifier = 'site-visit-form'

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        try:
            site_visit = Survey.objects.get(
                id=self.kwargs['sitevisitid']
            )
            if not site_visit.validated and site_visit.ready_for_validation:
                return False
            if (
                    site_visit.owner == self.request.user or
                    site_visit.collector_user == self.request.user
            ):
                return True
        except Survey.DoesNotExist:
            return False
        return False

    def remove_collection_records(self, excluded_collection_list):
        """
        Only superuser or staff can delete the existing records
        :param excluded_collection_list: list of excluded collection ids
        """
        if self.request.user.is_superuser or self.request.user.is_staff:
            collection_to_remove = BiologicalCollectionRecord.objects.filter(
                survey=self.object
            ).exclude(
                id__in=excluded_collection_list
            )
            if collection_to_remove.exists():
                collection_to_remove.delete()

    def _form_data(self, form, key, default_value=None):
        """
        Retrieves data from a form based on the specified key.
        Default value is returned if they key is not found
        :param form: The valid form data to retrieve the data
        :param key: The key in the form data to retrieve the value for
        :param default_value: The default value to return if the specified
            key is not found
        :return: The value from the form data for the specified key,
            or the default value if the key is not found
        """
        form_data = form.data.get(key, default_value)
        if not form_data and form_data != default_value:
            return default_value
        return form_data

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        collection_id_list = form.data.get('collection-id-list', '')
        collection_id_list = collection_id_list.split(',')
        collection_id_list = [x for x in collection_id_list if x != '']
        taxa_id_list = form.data.get('taxa-id-list', '')
        owner_id = form.data.get('owner_id', None)
        collector_id = form.data.get('collector_id', None)
        hydroperiod = form.data.get('hydroperiod', '')
        owner = None
        collector_user = None
        if owner_id:
            try:
                owner = get_user_model().objects.get(
                    id=int(owner_id))
            except get_user_model().DoesNotExist:
                owner = None

        if collector_id:
            try:
                collector_user = get_user_model().objects.get(
                    id=int(collector_id))
            except get_user_model().DoesNotExist:
                collector_user = None

        if collection_id_list:
            self.collection_records = BiologicalCollectionRecord.objects.filter(
                id__in=collection_id_list
            )
            for collection_record in self.collection_records:
                collection_record.present = (
                        form.data.get('{}-observed'.format(
                            collection_record.id
                        ), '') == 'on'
                )
                collection_record.abundance_number = (
                    float(form.data.get('{}-abundance'.format(
                        collection_record.id
                    ), 0))
                )
                sampling_effort = form.data.get('sampling_effort', '')
                if sampling_effort:
                    sampling_effort += (
                            ' ' + form.data.get('sampling_effort_type', '')
                    )
                    collection_record.sampling_effort = sampling_effort
                collection_record.save()
            self.collection_records.update(
                biotope_id=form.data.get('biotope', None),
                specific_biotope_id=form.data.get('specific_biotope', None),
                substratum_id=form.data.get('substratum', None),
                sampling_method_id=form.data.get('sampling_method', None),
                abundance_type=form.data.get('abundance_type', ''),
                owner=owner,
                collector_user=collector_user,
                hydroperiod=hydroperiod
            )

            # Remove deleted collection records
            self.remove_collection_records(
                excluded_collection_list=collection_id_list
            )

        # Check if there is a new collection record
        if taxa_id_list:
            taxa_id_list = taxa_id_list.split(',')
            taxa_id_list = filter(None, taxa_id_list)
            for taxon in taxa_id_list:
                observed_key = '{}-observed'.format(taxon)
                abundance_key = '{}-abundance'.format(taxon)
                taxonomy = Taxonomy.objects.get(
                    id=taxon
                )
                try:
                    if form.data[observed_key] == 'True':
                        abundance = form.data[abundance_key]
                        if abundance:
                            abundance = float(abundance)
                        else:
                            abundance = 0.0
                        collection_record, status = (
                            BiologicalCollectionRecord.objects.get_or_create(
                                collection_date=self.object.date,
                                taxonomy=taxonomy,
                                original_species_name=taxonomy.canonical_name,
                                site=self.object.site,
                                collector_user=collector_user,
                                sampling_method_id=self._form_data(
                                    form, 'sampling_method', None
                                ),
                                abundance_number=abundance,
                                owner=owner,
                                biotope_id=self._form_data(
                                    form, 'biotope', None
                                ),
                                specific_biotope_id=self._form_data(
                                    form, 'specific_biotope', None
                                ),
                                substratum_id=(
                                    self._form_data(
                                        form, 'substratum', None
                                    )
                                ),
                                reference=self._form_data(
                                    form, 'study_reference', ''
                                ),
                                reference_category=self._form_data(
                                    form, 'reference_category', ''
                                ),
                                sampling_effort=self._form_data(
                                    form, 'sampling_effort', ''
                                ),
                                abundance_type=self._form_data(
                                    form, 'abundance_type', ''
                                ),
                                survey=self.object,
                                record_type=self._form_data(
                                    form, 'record_type', ''
                                ),
                                hydroperiod=hydroperiod
                            )
                        )
                        if status:
                            print(
                                'Collection record added with id {}'.format(
                                    collection_record.id
                                )
                            )
                except KeyError:
                    continue

        # Add site image
        site_image_file = self.request.FILES.get('site-image', None)
        if site_image_file:
            site_image, _ = SiteImage.objects.get_or_create(
                survey=self.object,
                site=self.object.site
            )
            site_image.image = site_image_file
            site_image.save()

        if (
            not self.request.user.is_superuser and
            not self.request.user.is_staff and
            self.object.validated
        ):
            self.object.validated = False

        if self.collection_records:
            self.object.owner = self.collection_records.first().owner
            self.object.collector_user = (
                self.collection_records.first().collector_user
            )

        # -- Algae data
        curation_process = form.data.get('curation_process', None)
        indicator_chl_a = form.data.get('indicator_chl_a', None)
        indicator_afdm = form.data.get('indicator_afdm', None)
        ai = form.data.get('ai', '')
        if not ai:
            ai = None
        if curation_process or indicator_afdm or indicator_chl_a:
            algae_data = AlgaeData.objects.filter(
                survey=self.object
            )
            if algae_data.exists():
                if algae_data.count() > 1:
                    algae_data.exclude(id=algae_data[0].id).delete()
            else:
                AlgaeData.objects.create(survey=self.object)
                algae_data = AlgaeData.objects.filter(survey=self.object)
            algae_data.update(
                curation_process=curation_process,
                indicator_afdm=indicator_afdm,
                indicator_chl_a=indicator_chl_a,
                ai=ai
            )

        # -- Biomass chemical records
        chem_units = {}
        chl_type = form.data.get('chl_type', None)
        afdm_type = form.data.get('afdm_type', None)
        chl_a = form.data.get('chl_a', None)
        if chl_type and chl_a:
            chem_units[chl_type] = chl_a
            # Check existing data first, then remove it
            chla_codes = ['CHLA-B', 'CHLA-W']
            chla_records = ChemicalRecord.objects.filter(
                date=self.object.date,
                location_site=self.object.site,
                survey=self.object,
                chem__in=Chem.objects.filter(
                    chem_code__in=chla_codes
                )
            )
            if chla_records.exists():
                chla_records.delete()
        afdm = form.data.get('afdm', None)
        if afdm_type and afdm:
            chem_units[afdm_type] = afdm
            # Check existing data first, then remove it
            afdm_codes = ['AFDM-B', 'AFDM-W']
            afdm_records = ChemicalRecord.objects.filter(
                date=self.object.date,
                location_site=self.object.site,
                survey=self.object,
                chem__in=Chem.objects.filter(
                    chem_code__in=afdm_codes
                )
            )
            if afdm_records.exists():
                afdm_records.delete()
        for chem_unit in chem_units:
            chem = Chem.objects.filter(
                chem_code__iexact=chem_unit
            )
            if chem.exists():
                chem = chem[0]
            else:
                chem = Chem.objects.create(
                    chem_code=chem_unit
                )
            chem_record, _ = ChemicalRecord.objects.get_or_create(
                date=self.object.date,
                chem=chem,
                location_site=self.object.site,
                survey=self.object,
                value=chem_units[chem_unit]
            )

        return super(SiteVisitUpdateView, self).form_valid(form)

    def get_success_url(self):
        session_uuid = '%s' % uuid.uuid4()
        self.add_last_session(self.request, session_uuid, {
            'edited_at': int(time.mktime(libdatetime.now().timetuple())),
            'records': BiologicalCollectionRecord.objects.filter(
                survey=self.object
            ),
            'location_site': self.object.site,
            'form': 'site-visit-form'
        })
        source_reference_url = reverse('source-reference-form') + (
            '?session={session}&identifier={identifier}&next={next}'.format(
                session=session_uuid,
                next='/site-visit/detail/{}/'.format(self.object.id),
                identifier=self.session_identifier
            )
        )
        abiotic_url = '{base_url}?survey={survey_id}&next={next}'.format(
            base_url=reverse('abiotic-form'),
            survey_id=self.object.id,
            next=source_reference_url
        )
        return abiotic_url
