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
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.models.biotope import (
    Biotope,
)
from bims.models.sampling_method import SamplingMethod


class SiteVisitUpdateView(UserPassesTestMixin, UpdateView, SessionFormMixin):
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

    def taxon_group(self):
        """Get taxon group for the current site visit"""
        if self.collection_records.exists():
            return self.collection_records[0].taxonomy.taxongroup_set.filter(
                category=TaxonomicGroupCategory.SPECIES_MODULE.name
            )[0]
        return None

    def owner(self):
        """Get owner of the site visit"""
        if self.object.owner:
            return self.object.owner
        if self.collection_records.exists():
            return self.collection_records[0].owner
        return None

    def biotope(self, biotope_type):
        """Get a biotope from collection records"""
        biotope = self.collection_records.values(biotope_type)
        if biotope:
            try:
                return Biotope.objects.filter(id__in=biotope)[0]
            except IndexError:
                return None
        return None

    def sampling_method(self):
        """Get existing sampling method value from collections"""
        sampling_method = self.collection_records.values(
            'sampling_method'
        )
        if sampling_method:
            try:
                return SamplingMethod.objects.filter(
                    id__in=sampling_method
                )[0]
            except IndexError:
                return None
        return None

    def sampling_effort(self):
        """Get existing sampling effort value from collections"""
        sampling_effort = self.collection_records.exclude(
            sampling_effort=''
        )
        try:
            if sampling_effort.exists():
                sampling_effort_str = sampling_effort[0].sampling_effort
                sampling_effort_arr = sampling_effort_str.split(' ')
                return (
                    sampling_effort_arr[0].strip(),
                    sampling_effort_arr[1].strip()
                )
        except IndexError:
            pass
        return '', ''

    def abundance_type(self):
        """Get existing abundance type from collection"""
        abundance_type = self.collection_records.exclude(
            abundance_type=''
        )
        if abundance_type.exists():
            return abundance_type[0].abundance_type
        return None

    def source_reference(self):
        """Get existing source reference"""
        source_reference_records = self.collection_records.exclude(
            source_reference__isnull=True
        )
        if source_reference_records.exists():
            return source_reference_records[0].source_reference
        return None

    def get_context_data(self, **kwargs):
        context = super(SiteVisitUpdateView, self).get_context_data(**kwargs)
        self.collection_records = (
            BiologicalCollectionRecord.objects.filter(
                survey=self.object.id
            ).order_by('taxonomy__canonical_name')
        )
        context['source_reference'] = self.source_reference()
        context['collection_records'] = self.collection_records
        context['taxon_group'] = self.taxon_group()
        context['owner'] = self.owner()
        context['biotope'] = self.biotope('biotope')
        context['specific_biotope'] = self.biotope('specific_biotope')
        context['substratum'] = self.biotope('substratum')
        context['sampling_method'] = self.sampling_method()
        sampling_effort_value, sampling_effort_unit = self.sampling_effort()
        context['sampling_effort_value'] = sampling_effort_value
        context['sampling_effort_unit'] = sampling_effort_unit
        context['abundance_type'] = self.abundance_type()

        context['broad_biotope_list'] = (
            Biotope.objects.broad_biotope_list(
                taxon_group=context['taxon_group']
            )
        )
        context['specific_biotope_list'] = (
            Biotope.objects.specific_biotope_list(
                taxon_group=context['taxon_group']
            )
        )
        context['substratum_list'] = (
            Biotope.objects.substratum_list(
                taxon_group=context['taxon_group']
            )
        )
        context['sampling_method_list'] = (
            SamplingMethod.objects.sampling_method_list(
                taxon_group=context['taxon_group']
            )
        )
        return context

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
            abundance_type=form.data.get('abundance_type', '')
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
                next='/map',
                identifier=self.session_identifier
            )
        )
        abiotic_url = '{base_url}?survey={survey_id}&next={next}'.format(
            base_url=reverse('abiotic-form'),
            survey_id=self.object.id,
            next=source_reference_url
        )
        return abiotic_url
