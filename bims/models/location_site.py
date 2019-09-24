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
from django.conf import settings
from django.utils import timezone

from bims.models.location_type import LocationType
from bims.utils.get_key import get_key
from bims.models.document_links_mixin import DocumentLinksMixin
from bims.models.search_process import SearchProcess
from bims.enums.geomorphological_zone import GeomorphologicalZoneCategory
from bims.models.location_context import LocationContext


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
    legacy_site_code = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    location_type = models.ForeignKey(
        LocationType,
        models.CASCADE,
        null=False,
    )
    refined_geomorphological = models.CharField(
        blank=True,
        null=True,
        max_length=200,
        choices=[(g.value, g.value) for g in GeomorphologicalZoneCategory],
        help_text='Would be used in preference to the one discovered '
                  'in geocontext',
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

    latitude = models.FloatField(
        blank=True,
        help_text='Latitude of location site',
        null=True
    )

    longitude = models.FloatField(
        blank=True,
        help_text='Longitude of location site',
        null=True
    )
    original_geomorphological = models.CharField(
        blank=True,
        null=True,
        max_length=200,
        help_text='Original geomorphological zone from spatial layer'
    )

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        related_name='site_creator',
        help_text='The creator of the site',
        blank=True,
        null=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        related_name='site_owner',
        help_text='The owner of the site',
        blank=True,
        null=True,
    )

    def location_context_group_values(self, group_name):
        """
        Returns location group data by group name
        :param group_name: string of group name, e.g. geomorphological_group
        :return: dict of group data
        """
        try:
            location_context = json.loads(self.location_context)
        except ValueError:
            return {}
        try:
            return (
                location_context
                ['context_group_values']
                [group_name]
                ['service_registry_values']
            )
        except KeyError:
            return {}

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
        LOGGER.info('Request url : {}'.format(url))

        r = requests.get(url)
        if r.status_code != 200:
            message = (
                    'Request to url %s got %s [%s], can not update location '
                    'context document.' % (url, r.status_code, r.reason))
            LOGGER.info(message)
            return None

        return json.dumps(r.json())

    def add_context_group(self, group_key):
        from bims.models import LocationContext
        geocontext_data_string = self.get_geocontext_group_data(group_key)
        try:
            geocontext_data = json.loads(geocontext_data_string)
            for geocontext_value in geocontext_data['service_registry_values']:
                if not geocontext_value['value']:
                    continue
                location_context, created = (
                    LocationContext.objects.get_or_create(
                        site=self,
                        key=geocontext_value['key'],
                    )
                )
                location_context.name = geocontext_value['name']
                location_context.group_key = geocontext_data['key']
                location_context.fetch_time = timezone.now()
                location_context.value = str(geocontext_value['value'])
                location_context.save()
        except (ValueError, KeyError, TypeError):
            return False, 'Could not format the geocontext data'
        return True, 'Added'

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
        lon_lat_changed = False

        self.additional_data = self.validate_json_field(
            self.additional_data
        )
        self.location_context_document = self.validate_json_field(
            self.location_context_document
        )
        self.location_context = self.validate_json_field(
            self.location_context
        )

        """Check if one of geometry is not null."""
        if self.geometry_point or self.geometry_line or \
                self.geometry_polygon or self.geometry_multipolygon:
            # Check if geometry is allowed
            if isinstance(self.get_geometry(),
                          self.location_type.get_allowed_geometry_class()):
                if (
                        self.get_centroid().x != self.__original_longitude or
                        not self.longitude
                ):
                    self.longitude = self.get_centroid().x
                    lon_lat_changed = True
                if (
                        self.get_centroid().y != self.__original_latitude or
                        not self.latitude
                ):
                    self.latitude = self.get_centroid().y
                    lon_lat_changed = True

                # Check if latitude or longitude changed manually
                if (
                        self.latitude != self.__original_latitude or
                        self.longitude != self.__original_longitude
                ):
                    if not lon_lat_changed:
                        self.geometry_point.x = self.longitude
                        self.geometry_point.y = self.latitude
                super(LocationSite, self).save(*args, **kwargs)
                self.__original_centroid = self.get_centroid()
            else:
                raise ValidationError('Geometry is not allowed.')
        else:
            raise ValidationError('At least one geometry need to be filled.')

        if (
                self.__original_refined_geomorphological !=
                self.refined_geomorphological):
            SearchProcess.objects.filter(
                finished=True
            ).delete()

    def __init__(self, *args, **kwargs):
        super(LocationSite, self).__init__(*args, **kwargs)
        self.__original_centroid = self.get_centroid()
        self.__original_refined_geomorphological = (
            self.refined_geomorphological
        )
        self.__original_latitude = self.latitude
        self.__original_longitude = self.longitude


@receiver(models.signals.post_save)
def location_site_post_save_handler(sender, instance, **kwargs):
    """
    Update cluster when location site saved
    """
    if not issubclass(sender, LocationSite):
        return
    models.signals.post_save.disconnect(
        location_site_post_save_handler,
    )

    # Update refined geomorphological if exist
    if instance.refined_geomorphological:
        try:
            try:
                geo_context, created = LocationContext.objects.get_or_create(
                    site=instance,
                    key='geo_class_recoded',
                )
            except LocationContext.MultipleObjectsReturned:
                LocationContext.objects.filter(
                    site=instance,
                    key='geo_class_recoded'
                ).delete()
                geo_context = LocationContext.objects.create(
                    site=instance,
                    key='geo_class_recoded'
                )
                created = True
            geo_context.name = 'Geomorphological zones'
            geo_context.group_key = 'geomorphological_group'
            if not created:
                if instance.refined_geomorphological != geo_context.value:
                    instance.original_geomorphological = geo_context.value
                    geo_context.value = instance.refined_geomorphological
                    geo_context.save()
            else:
                geo_context.value = instance.refined_geomorphological
                geo_context.save()
            if not instance.original_geomorphological:
                instance.original_geomorphological = geo_context.value
            instance.save()
        except LocationContext.MultipleObjectsReturned:
            pass

    models.signals.post_save.connect(
        location_site_post_save_handler
    )
