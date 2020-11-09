import time
import uuid
from datetime import datetime as libdatetime
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
    collection_records = None
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
            if (
                    site_visit.owner == self.request.user or
                    site_visit.collector_user == self.request.user
            ):
                return True
        except Survey.DoesNotExist:
            return False
        return False

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        collection_id_list = form.data.get('collection-id-list', '')
        collection_id_list = collection_id_list.split(',')
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
            biotope=form.data.get('biotope', None),
            specific_biotope=form.data.get('specific_biotope', None),
            substratum=form.data.get('substratum', None),
            sampling_method=form.data.get('sampling_method', None),
            abundance_type=form.data.get('abundance_type', ''),
            owner=form.data.get('owner_id', None)
        )

        # Add site image
        site_image_file = self.request.FILES.get('site-image', None)
        if site_image_file:
            site_image, _ = SiteImage.objects.get_or_create(
                survey=self.object,
                site=self.object.site
            )
            site_image.image = site_image_file
            site_image.save()

        self.object.validated = False
        self.object.owner = self.collection_records[0].owner
        self.object.collector_user = self.collection_records[0].collector_user

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
        afdm = form.data.get('afdm', None)
        if afdm_type and afdm:
            chem_units[afdm_type] = afdm
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
