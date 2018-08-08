# coding=utf-8
"""Forms to upload shapefile.
"""

from django import forms
from bims.models.shapefile import Shapefile


class ShapefileUploadForm(forms.ModelForm):
    """Shapefile upload form"""

    token = ''

    class Meta:
        model = Shapefile
        fields = ('shapefile', 'token')

    def save(self, commit=True):
        self.instance.token = self.token
        return super(ShapefileUploadForm, self).save(commit=commit)
