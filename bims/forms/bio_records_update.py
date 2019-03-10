# coding=utf-8
from django.contrib.gis import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout,
    Fieldset,
    Field,
)
from bims.models import BiologicalCollectionRecord


class BioRecordsForm(forms.ModelForm):
    class Meta:
        model = BiologicalCollectionRecord
        fields = (
            'original_species_name',
            'category',
            'present',
            'absent',
            'collection_date',
            'notes',
            'taxonomy',
            'ready_for_validation',
        )

    def __init__(self, *args, **kwargs):
        form_title = ''
        self.helper = FormHelper()
        layout = Layout(
            Fieldset(
                form_title,
                Field('original_species_name', css_class='form-control'),
                Field('ready_for_validation', css_class='form-control'),
                Field('category', css_class='form-control'),
                Field('present', css_class='form-control'),
                Field('absent', css_class='form-control'),
                Field('collection_date', css_class='form-control'),
                Field('notes', css_class='form-control'),
                Field('taxonomy', css_class='form-control'),
            )
        )
        self.helper.layout = layout
        self.helper.html5_required = False
        self.helper.form_tag = False
        super(BioRecordsForm, self).__init__(*args, **kwargs)
