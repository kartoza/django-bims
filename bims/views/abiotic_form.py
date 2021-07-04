import json
from django.views.generic import TemplateView
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.mixins import UserPassesTestMixin
from sass.enums.chem_unit import ChemUnit
from bims.serializers.survey_serializer import SurveyDataSerializer
from bims.templatetags.site_visit_extras import get_unvalidated_site_visits_url
from bims.models import (
    Survey,
    ChemicalRecord,
    Chem,
    SurveyData,
    SurveyDataOption,
    SurveyDataValue,
    BiologicalCollectionRecord
)


class AbioticFormView(UserPassesTestMixin, TemplateView):
    template_name = 'abiotic/abiotic_form.html'
    update_form = False
    chemical_records = None
    survey = None

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.method == 'GET':
            survey_id = self.request.GET.get('survey', None)
        else:
            survey_id = self.request.POST.get('survey_id', None)
        if not survey_id:
            raise Http404('Missing survey id')
        if self.request.user.is_superuser:
            return True
        if Survey.objects.filter(
            owner=self.request.user,
            id=survey_id
        ).exists():
            return True
        if BiologicalCollectionRecord.objects.filter(
            Q(owner=self.request.user) |
            Q(collector_user=self.request.user)
        ).exists():
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super(AbioticFormView, self).get_context_data(**kwargs)
        context['chemical_records'] = []
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
            try:
                chem_unit = ChemUnit[chem.chem_unit].value
            except KeyError:
                chem_unit = chem.chem_unit
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

        if self.survey:
            context['survey_id'] = self.survey.id
            context['site_code'] = self.survey.site.location_site_identifier
            context['survey_date'] = self.survey.date.strftime(
                '%Y-%m-%d'
            )
            context['survey_data_list'] = (
                SurveyDataSerializer(
                    SurveyData.objects.all().order_by(
                        'display_order'
                    ), many=True, context={'survey_id': self.survey.id}
                ).data
            )
        context['update_form'] = self.update_form
        context['CHEM_UNITS'] = ChemUnit.__members__
        return context

    def get(self, request, *args, **kwargs):
        survey_id = self.request.GET.get('survey')
        try:
            self.survey = Survey.objects.get(
                id=survey_id
            )
        except Survey.DoesNotExist:
            raise Http404('Survey does not exist')
        if not self.survey.owner:
            self.survey.owner = self.request.user
            self.survey.save()
        _chemical_records = ChemicalRecord.objects.filter(
            survey=self.survey
        )
        if _chemical_records.exists():
            self.chemical_records = _chemical_records
            self.update_form = True

        return super(AbioticFormView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        post_data = request.POST.dict()
        survey_id = post_data.get('survey_id', None)
        redirect_path = post_data.get('next', '')
        if not redirect_path:
            redirect_path = get_unvalidated_site_visits_url(request.user)
        survey = None
        if survey_id:
            try:
                survey = Survey.objects.get(id=survey_id)
            except Survey.DoesNotExist:
                pass
        if not survey:
            raise Http404('Missing survey')
        chemical_record_json = post_data.get('abiotic_data', None)
        if not chemical_record_json:
            raise Http404('No abiotic data')
        try:
            chemical_records = json.loads(chemical_record_json)
        except ValueError:
            raise Http404('Invalid format of abiotic data')

        # Survey data
        survey_data_value = []
        for post_data_key in post_data:
            if 'survey_data_' in post_data_key:
                try:
                    survey_data_id = (
                        post_data_key.split(
                            'survey_data_'
                        )[1]
                    )
                    survey_data = SurveyData.objects.get(
                        id=int(survey_data_id)
                    )
                    survey_data_option = SurveyDataOption.objects.get(
                        id=int(post_data[post_data_key])
                    )
                    value, created = SurveyDataValue.objects.get_or_create(
                        survey=survey,
                        survey_data=survey_data,
                        survey_data_option=survey_data_option
                    )
                    survey_data_value.append(value.id)
                except (SurveyData.DoesNotExist, IndexError, ValueError):
                    continue
        if survey_data_value:
            SurveyDataValue.objects.filter(survey=survey).exclude(
                id__in=survey_data_value
            ).delete()

        updated_record_ids = []

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
                    date=survey.date
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
