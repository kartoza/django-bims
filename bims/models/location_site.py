# coding=utf-8
"""Site model definition.

"""

import logging
import requests

from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from django.dispatch import receiver
from bims.models.location_type import LocationType
from bims.models.location_context import LocationContext
from bims.utils.cluster import update_cluster_by_site
from bims.utils.get_key import get_key

LOGGER = logging.getLogger(__name__)


class LocationSite(models.Model):
    """Location Site model."""

    name = models.CharField(
        max_length=100,
        blank=False,
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
    location_context = models.ForeignKey(
        LocationContext,
        models.SET_NULL,
        null=True,
        blank=True,
    )

    location_context_document = models.TextField(
        verbose_name='Document for location context as JSON.',
        help_text='This document is generated from GeoContext by using '
                  'management command or changing the geometry.',
        null=True,
        blank=True
    )

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

    def update_location_context_document(self):
        """Update location context document."""
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
        longitude = self.get_centroid().get_x()
        latitude = self.get_centroid().get_x()

        # build url
        url_format = '{geocontext_url}/api/v1/geocontext/value/collection/' \
                     '{longitude}/{latitude}/{geocontext_collection_key}'
        url = url_format.format(
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

        self.location_context_document = r.json()
        self.save()
        return True, 'Successfully update location context document.'

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'

    def __str__(self):
        return u'%s' % self.name

    def save(self, *args, **kwargs):
        """Check if one of geometry is not null."""
        if self.geometry_point or self.geometry_line or \
                self.geometry_polygon or self.geometry_multipolygon:
            # Check if geometry is allowed
            if isinstance(self.get_geometry(),
                          self.location_type.get_allowed_geometry_class()):
                super(LocationSite, self).save(*args, **kwargs)
            else:
                raise ValidationError('Geometry is not allowed.')
        else:
            raise ValidationError('At least one geometry need to be filled.')


@receiver(models.signals.post_save)
def location_site_post_save_handler(sender, instance, **kwargs):
    """
    Update cluster when location site saved
    """
    if not issubclass(sender, LocationSite):
        return
    update_cluster_by_site(instance)
