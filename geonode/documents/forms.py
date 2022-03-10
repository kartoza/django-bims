import logging
import os
import json

from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings
from django.forms import HiddenInput
from modeltranslation.forms import TranslationModelForm
from geonode.documents.models import (
    Document,
)
logger = logging.getLogger(__name__)


class DocumentCreateForm(TranslationModelForm):

    """
    The document upload form.
    """
    permissions = forms.CharField(
        widget=HiddenInput(
            attrs={
                'name': 'permissions',
                'id': 'permissions'}),
        required=True)

    links = forms.MultipleChoiceField(
        label=_("Link to"),
        required=False)

    class Meta:
        model = Document
        fields = ['title', 'doc_file', 'doc_url']
        widgets = {
            'name': HiddenInput(attrs={'cols': 80, 'rows': 20}),
        }

    def __init__(self, *args, **kwargs):
        super(DocumentCreateForm, self).__init__(*args, **kwargs)
        self.fields['links'].choices = self.generate_link_choices()

    def clean_permissions(self):
        """
        Ensures the JSON field is JSON.
        """
        permissions = self.cleaned_data['permissions']

        try:
            return json.loads(permissions)
        except ValueError:
            raise forms.ValidationError(_("Permissions must be valid JSON."))

    def clean(self):
        """
        Ensures the doc_file or the doc_url field is populated.
        """
        cleaned_data = super(DocumentCreateForm, self).clean()
        doc_file = self.cleaned_data.get('doc_file')
        doc_url = self.cleaned_data.get('doc_url')

        if not doc_file and not doc_url:
            logger.debug("Document must be a file or url.")
            raise forms.ValidationError(_("Document must be a file or url."))

        if doc_file and doc_url:
            logger.debug("A document cannot have both a file and a url.")
            raise forms.ValidationError(
                _("A document cannot have both a file and a url."))

        return cleaned_data

    def clean_doc_file(self):
        """
        Ensures the doc_file is valid.
        """
        doc_file = self.cleaned_data.get('doc_file')

        if doc_file and not os.path.splitext(
                doc_file.name)[1].lower()[
                1:] in settings.ALLOWED_DOCUMENT_TYPES:
            logger.debug("This file type is not allowed")
            raise forms.ValidationError(_("This file type is not allowed"))

        return doc_file
