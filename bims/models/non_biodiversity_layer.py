# coding=utf-8
"""Non biodiversity layer model definition.
"""
from django.contrib.sites.models import Site
from django.db import models
from ordered_model.models import OrderedModel


class NonBiodiversityLayer(OrderedModel):
    """Non biodiversity layer model."""
    name = models.CharField(
        max_length=100,
        unique=True
    )
    wms_url = models.CharField(
        max_length=256,
        blank=True,
        verbose_name='Url'
    )
    wms_layer_name = models.CharField(
        max_length=128,
        verbose_name='Layer name'
    )
    wms_format = models.CharField(
        max_length=64,
        default='image/png',
        blank=True,
        verbose_name='Layer format'
    )
    layer_style = models.CharField(
        max_length=256,
        default='',
        help_text='Leave blank to use default style',
        blank=True,
        verbose_name='External layer style name'
    )
    native_layer = models.ForeignKey(
        'cloud_native_gis.Layer',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    native_layer_style = models.ForeignKey(
        'cloud_native_gis.Style',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    default_visibility = models.BooleanField(
        default=False
    )
    get_feature_format = models.TextField(
        max_length=100,
        default='text/plain'
    )
    csv_file = models.FileField(
        upload_to='non_biodiversity_layer_csv_file',
        null=True,
        blank=True,
        help_text='A CSV file that will be filtered and downloaded based on '
                  'matching values between "layer_csv_attribute" '
                  'and "csv_attribute". This will also show the download '
                  'button in the attribute data panel.'
    )
    csv_attribute = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text='Column name in the csv that will be used to '
                  'filter csv_file.'
    )

    layer_csv_attribute = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text='Attribute in the layer that will be used '
                  'to filter csv_file.'
    )

    document = models.FileField(
        upload_to='non_biodiversity_layer_document',
        null=True,
        blank=True,
        help_text='File to be displayed as an attachment in the attribute popup.'
    )

    document_title = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text='Title for the attached document. Displayed on the download button.'
    )

    enable_styles_selection = models.BooleanField(
        default=False,
        verbose_name='Enable styles selection',
        help_text='Check this box to show the styles selection '
                  'in the layer selector.'
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        ordering = ('order',)
