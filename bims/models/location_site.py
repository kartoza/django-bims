# coding=utf-8
"""Site model definition.

"""

import logging
import requests
import json

from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField
from bims.models.boundary import Boundary
from bims.models.location_type import LocationType
from bims.utils.get_key import get_key
from bims.models.document_links_mixin import DocumentLinksMixin

LOGGER = logging.getLogger(__name__)


class LocationSite(DocumentLinksMixin):
    """Location Site model."""

    __original_centroid = None
    geocontext_url_format = '{geocontext_url}/api/v1/geocontext/value/' \
                            'collection/{longitude}/{latitude}/' \
                            '{geocontext_collection_key}'

    name = models.CharField(
        max_length=300,
        blank=False,
    )
    site_description = models.CharField(
        max_length=500,
        blank=True,
        default=''
    )
    site_code = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    location_type = models.ForeignKey(
        LocationType,
        models.CASCADE,
        null=False,
    )
    geometry_point = models.PointField(
        null=True,
        blank=True,
    )
    geometry_line = models.LineStringField(
        null=True,
        blank=True,
    )
    geometry_polygon = models.PolygonField(
        null=True,
        blank=True,
    )
    geometry_multipolygon = models.MultiPolygonField(
        null=True,
        blank=True,
    )
    map_reference = models.CharField(
        null=True,
        blank=True,
        max_length=200
    )
    land_owner_detail = models.TextField(
        null=True,
        blank=True,
    )
    river = models.ForeignKey(
        'sass.River',
        null=True,
        blank=True,
    )

    location_context_document = JSONField(
        verbose_name='Document for location context as JSON.',
        help_text='This document is generated from GeoContext by using '
                  'management command or changing the geometry.',
        null=True,
        blank=True
    )

    location_context = JSONField(
        verbose_name='Formatted location_context_document',
        help_text='This is intended for filtering',
        null=True,
        blank=True
    )

    additional_data = JSONField(
        verbose_name='Additional json data',
        null=True,
        blank=True
    )

    boundary = models.ForeignKey(
        Boundary,
        help_text='This is lowest boundary where location is placed.',
        blank=True,
        null=True,
    )

    latitude = models.FloatField(
        blank=True,
        help_text='This is intended only for IPT',
        null=True
    )

    longitude = models.FloatField(
        blank=True,
        help_text='This is intended only for IPT',
        null=True
    )

    def get_site_detail_info(self):
        """ Getting data for overview panel site_detail_info widget """
        

    def get_centroid(self):
        """ Getting centroid of location site """

        if self.geometry_point:
            return self.geometry_point
        else:
            if self.get_geometry():
                return self.get_geometry().centroid
            else:
                return None

    def get_geometry(self):
        """Function to get geometry."""
        geometry = None
        validation_error = ValidationError('Only one geometry allowed.')

        if self.geometry_point:
            if geometry:
                raise validation_error
            geometry = self.geometry_point

        if self.geometry_polygon:
            if geometry:
                raise validation_error
            geometry = self.geometry_polygon

        if self.geometry_multipolygon:
            if geometry:
                raise validation_error
            geometry = self.geometry_multipolygon

        if self.geometry_line:
            if geometry:
                raise validation_error
            geometry = self.geometry_line

        return geometry

    def get_geocontext_group_data(self, group_key):
        LOGGER.debug('get_location_group_data for ' + group_key)
        geocontext_url = get_key('GEOCONTEXT_URL')
        if not geocontext_url:
            message = (
                'Can not update location context document because geocontext '
                'url is None. Please set it.')
            return False, message
        if not self.get_centroid():
            message = (
                'Can not update location context document because centroid is '
                'None. Please set it.')
            return False, message
        longitude = self.get_centroid().x
        latitude = self.get_centroid().y

        geocontext_group_url_format = (
            '{geocontext_url}/api/v1/geocontext/value/group/'
            '{longitude}/{latitude}/{geocontext_group_key}')
        # build url
        url = geocontext_group_url_format.format(
            geocontext_url=geocontext_url,
            longitude=longitude,
            latitude=latitude,
            geocontext_group_key=group_key,
        )

        r = requests.get(url)
        if r.status_code != 200:
            message = (
                    'Request to url %s got %s [%s], can not update location '
                    'context document.' % (url, r.status_code, r.reason))
            LOGGER.info(message)
            return None

        return json.dumps(r.json())

    def add_context_group(self, group_key):
        old_location_context_string = self.location_context_document
        old_location_context = None
        if old_location_context_string:
            try:
                old_location_context = json.loads(old_location_context_string)
            except ValueError:
                LOGGER.info('No JSON Object')
        new_data = self.get_geocontext_group_data(group_key)
        if not new_data:
            return False, "Error from GeoContext"
        if not old_location_context:
            old_location_context_string = (
                '{"context_group_values":[%s]}' % new_data)
            self.location_context_document = old_location_context_string
            return True, "Group values added to empty document"
        new_context_data = json.loads(new_data)
        key = new_context_data['key']
        data_exists = False
        return_message = ''
        for context_group in old_location_context['context_group_values']:
            if context_group['key'] == key:
                return_message = 'Group value updated'
                data_exists = True
                context_group['service_registry_values'] = (
                    new_context_data['service_registry_values']
                )
        if not data_exists:
            return_message = 'Group values added'
            old_location_context['context_group_values'].append(
                new_context_data
            )
        self.location_context_document = json.dumps(old_location_context)
        return True, return_message

    def clear_location_context_document(self):
        self.location_context_document = ""
        return True, "Document cleared"

    def update_location_context_document(self):
        """Update location context document."""
        LOGGER.debug('update_location_context_document')
        geocontext_url = get_key('GEOCONTEXT_URL')
        geocontext_collection_key = get_key('GEOCONTEXT_COLLECTION_KEY')
        if not geocontext_url:
            message = (
                'Can not update location context document because geocontext '
                'url is None. Please set it.')
            return False, message
        if not geocontext_collection_key:
            message = (
                'Can not update location context document because geocontext '
                'collection key is None. Please set it.')
            return False, message
        if not self.get_centroid():
            message = (
                'Can not update location context document because centroid is '
                'None. Please set it.')
            return False, message
        longitude = self.get_centroid().x
        latitude = self.get_centroid().y

        # build url
        url = self.geocontext_url_format.format(
            geocontext_url=geocontext_url,
            longitude=longitude,
            latitude=latitude,
            geocontext_collection_key=geocontext_collection_key,
        )

        r = requests.get(url)
        if r.status_code != 200:
            message = (
                'Request to url %s got %s [%s], can not update location '
                'context document.' % (url, r.status_code, r.reason))
            return False, message

        self.location_context_document = json.dumps(r.json())
        return True, 'Successfully update location context document.'

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'

    def __unicode__(self):
        return u'%s' % self.name

    def validate_json_field(self, field):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        while not is_dictionary and attempt < max_allowed:
            if not field:
                break
            if isinstance(field, dict):
                is_dictionary = True
            else:
                field = json.loads(
                    field
                )
                attempt += 1
        return field

    def save(self, *args, **kwargs):
        """Check if one of geometry is not null."""
        self.additional_data = self.validate_json_field(
            self.additional_data
        )
        self.location_context_document = self.validate_json_field(
            self.location_context_document
        )
        self.location_context = self.validate_json_field(
            self.location_context
        )

        if self.geometry_point or self.geometry_line or \
                self.geometry_polygon or self.geometry_multipolygon:
            # Check if geometry is allowed
            if isinstance(self.get_geometry(),
                          self.location_type.get_allowed_geometry_class()):
                self.longitude = self.get_centroid().x
                self.latitude = self.get_centroid().y
                super(LocationSite, self).save(*args, **kwargs)
                self.__original_centroid = self.get_centroid()
            else:
                raise ValidationError('Geometry is not allowed.')
        else:
            raise ValidationError('At least one geometry need to be filled.')

    def __init__(self, *args, **kwargs):
        super(LocationSite, self).__init__(*args, **kwargs)
        self.__original_centroid = self.get_centroid()


@receiver(models.signals.post_save)
def location_site_post_save_handler(sender, instance, **kwargs):
    """
    Update cluster when location site saved
    """
    from bims.utils.location_context import format_location_context
    if not issubclass(sender, LocationSite):
        return
    format_location_context(instance.id)
