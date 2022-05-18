import json
from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.functions import Lower
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from bims.models import Chem, LocationSite, BaseMapLayer, ChemicalRecord, \
    Survey, SourceReference
from bims.templatetags import get_unvalidated_site_visits_url
from bims.utils.get_key import get_key
from sass.enums.chem_unit import ChemUnit


class PhysicoChemicalView(UserPassesTestMixin, TemplateView):
    """View for water temperature form"""
    template_name = 'physico_chemical_form.html'
    permission = 'bims.create_physico_chemical'
    location_site = LocationSite.objects.none
    update_form = False

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.has_perm(self.permission)

    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site = get_object_or_404(
                LocationSite,
                pk=site_id
            )
        else:
            raise Http404()

        return super(
            PhysicoChemicalView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PhysicoChemicalView, self).get_context_data(**kwargs)
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        context['location_site_name'] = self.location_site.name
        context['location_site_code'] = self.location_site.site_code
        context['location_site_lat'] = self.location_site.get_centroid().y
        context['location_site_long'] = self.location_site.get_centroid().x
        context['site_id'] = self.location_site.id
        context['chemical_records'] = []

        try:
            context['bing_key'] = BaseMapLayer.objects.get(
                source_type='bing').key
        except BaseMapLayer.DoesNotExist:
            context['bing_key'] = ''

        for chem in Chem.objects.filter(
                show_in_abiotic_list=True
        ).order_by(Lower('chem_description')):
            value = 0
            record_id = None
            if self.update_form:
                chem_data = self.chemical_records.filter(chem=chem)
                if chem_data.exists():
                    chem_data = chem_data[0]
                    value = chem_data.value
                    record_id = chem_data.id
            chem_unit = chem.chem_unit.unit
            context['chemical_records'].append({
                'chem_unit': chem.id,
                'chem_record_id': record_id,
                'description': (
                    chem.chem_description
                    if chem.chem_description else
                    chem.chem_code
                ),
                'unit': chem_unit,
                'max': chem.maximum,
                'min': chem.minimum,
                'value': value
            })

        context['CHEM_UNITS'] = ChemUnit.__members__
        return context

    def post(self, request, *args, **kwargs):
        post_data = request.POST.dict()
        site_id = post_data.get('site-id', None)
        date_string = request.POST.get('date', None)
        owner_id = request.POST.get('owner_id', '').strip()
        redirect_path = post_data.get('next', '')
        source_reference_id = request.POST.get('source_reference', '')
        source_reference = None

        if not redirect_path:
            redirect_path = get_unvalidated_site_visits_url(request.user)
        chemical_record_json = post_data.get('physico-chemical-data', None)
        if not chemical_record_json:
            raise Http404('No chemical data')
        try:
            chemical_records = json.loads(chemical_record_json)
        except ValueError:
            raise Http404('Invalid format of abiotic data')

        location_site = LocationSite.objects.get(id=site_id)

        updated_record_ids = []
        collection_date = parse(date_string)

        if source_reference_id:
            try:
                source_reference = SourceReference.objects.get(
                    id=source_reference_id
                )
            except SourceReference.DoesNotExist:
                pass

        # If collector id exist then get the user object
        owner = None
        if owner_id:
            try:
                owner = get_user_model().objects.get(
                    id=int(owner_id))
            except get_user_model().DoesNotExist:
                pass
        else:
            owner = self.request.user

        survey = Survey.objects.create(
            owner=owner,
            date=collection_date,
            site=location_site,
            collector_user=self.request.user,
            validated=False,
            ready_for_validation=True
        )

        for chem_unit in chemical_records:
            chemical_record_value = chemical_records[chem_unit]
            if not chemical_record_value:
                chemical_record_value = 0
            try:
                chem_unit = Chem.objects.get(
                    id=chem_unit
                )
                existing_chemical_records = ChemicalRecord.objects.filter(
                    chem=chem_unit,
                    survey=survey,
                    date=survey.date
                )
                if existing_chemical_records.count() > 1:
                    # This shouldn't be happening, but just in case
                    chemical_record = existing_chemical_records[0]
                    ChemicalRecord.objects.filter(
                        id__in=existing_chemical_records
                    ).exclude(
                        id=chemical_record.id
                    ).delete()

                record, created = ChemicalRecord.objects.get_or_create(
                    chem=chem_unit,
                    survey=survey,
                    date=survey.date,
                    source_reference=source_reference
                )
                updated_record_ids.append(record.id)
                record.value = float(chemical_record_value)
                record.save()
            except Chem.DoesNotExist:
                continue

        # Remove chemical record that is not on the updated list
        ChemicalRecord.objects.filter(
            survey=survey
        ).exclude(id__in=updated_record_ids).delete()

        return HttpResponseRedirect(redirect_path)
