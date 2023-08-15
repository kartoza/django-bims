# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import re
import logging

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.db.models import Q
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager
from mptt.models import MPTTModel, TreeForeignKey

from taggit.models import TagBase, ItemBase
from taggit.managers import TaggableManager, _TaggableManager
from treebeard.mp_tree import MP_Node, MP_NodeQuerySet, MP_NodeManager

from geonode.base.enumerations import (
    ALL_LANGUAGES,
    HIERARCHY_LEVELS,
    UPDATE_FREQUENCIES,
    DEFAULT_SUPPLEMENTAL_INFORMATION)
from geonode.people.enumerations import ROLE_VALUES

from geonode.notifications_helper import (
    send_notification,
    get_notification_recipients)
from geonode.groups.models import GroupProfile

logger = logging.getLogger(__name__)


class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Profiles as Contacts to Resources and apply roles.
    """
    resource = models.ForeignKey('ResourceBase', blank=False, null=False, on_delete=models.CASCADE)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        choices=ROLE_VALUES,
        max_length=255,
        help_text=_(
            'function performed by the responsible '
            'party'))

    def clean(self):
        """
        Make sure there is only one poc and author per resource
        """

        if not hasattr(self, 'resource'):
            # The ModelForm will already raise a Validation error for a missing resource.
            # Re-raising an empty error here ensures the rest of this method isn't
            # executed.
            raise ValidationError('')

        if self.role == self.resource.poc:
            contacts = self.resource.contacts.filter(
                contactrole__role=self.role)
            if contacts.count() == 1:
                # only allow this if we are updating the same contact
                if self.contact != contacts.get():
                    raise ValidationError(
                        'There can be only one %s for a given resource' %
                        self.role)
        if self.contact is None:
            # verify that any unbound contact is only associated to one
            # resource
            bounds = ContactRole.objects.filter(contact=self.contact).count()
            if bounds > 1:
                raise ValidationError(
                    'There can be one and only one resource linked to an unbound contact' %
                    self.role)
            elif bounds == 1:
                # verify that if there was one already, it corresponds to this
                # instance
                if ContactRole.objects.filter(
                        contact=self.contact).get().id != self.id:
                    raise ValidationError(
                        'There can be one and only one resource linked to an unbound contact' %
                        self.role)

    class Meta:
        unique_together = (("contact", "resource", "role"),)


class TopicCategory(models.Model):
    """
    Metadata about high-level geographic data thematic classification.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_MD_TopicCategoryCode">
    """
    identifier = models.CharField(max_length=255, default='location')
    description = models.TextField(default='')
    gn_description = models.TextField(
        'GeoNode description', default='', null=True)
    is_choice = models.BooleanField(default=True)
    fa_class = models.CharField(max_length=64, default='fa-times')

    def __str__(self):
        return self.gn_description

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Metadata Topic Categories'


class SpatialRepresentationType(models.Model):
    """
    Metadata information about the spatial representation type.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_SpatialRepresentationTypeCode">
    """
    identifier = models.CharField(max_length=255, editable=False)
    description = models.CharField(max_length=255, editable=False)
    gn_description = models.CharField('GeoNode description', max_length=255)
    is_choice = models.BooleanField(default=True)

    def __str__(self):
        return "{0}".format(self.gn_description)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Metadata Spatial Representation Types'


class ResourceBaseManager(PolymorphicManager):
    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = get_user_model().objects.filter(is_superuser=True).order_by('id')
        if superusers.count() == 0:
            raise RuntimeError(
                'GeoNode needs at least one admin/superuser set')

        return superusers[0]

    def get_queryset(self):
        return super(
            ResourceBaseManager,
            self).get_queryset().non_polymorphic()

    def polymorphic_queryset(self):
        return super(ResourceBaseManager, self).get_queryset()



class HierarchicalKeywordQuerySet(MP_NodeQuerySet):
    """QuerySet to automatically create a root node if `depth` not given."""

    def create(self, **kwargs):
        if 'depth' not in kwargs:
            return self.model.add_root(**kwargs)
        return super(HierarchicalKeywordQuerySet, self).create(**kwargs)


class HierarchicalKeywordManager(MP_NodeManager):

    def get_queryset(self):
        return HierarchicalKeywordQuerySet(self.model).order_by('path')


class HierarchicalKeyword(TagBase, MP_Node):
    node_order_by = ['name']

    objects = HierarchicalKeywordManager()


class _HierarchicalTagManager(_TaggableManager):
    def add(self, *tags):
        str_tags = set([
            t
            for t in tags
            if not isinstance(t, self.through.tag_model())
        ])
        tag_objs = set(tags) - str_tags
        # If str_tags has 0 elements Django actually optimizes that to not do a
        # query.  Malcolm is very smart.
        existing = self.through.tag_model().objects.filter(
            name__in=str_tags
        )
        tag_objs.update(existing)
        for new_tag in str_tags - set(t.name for t in existing):
            if new_tag:
                new_tag = escape(new_tag)
                tag_objs.add(HierarchicalKeyword.add_root(name=new_tag))

        for tag in tag_objs:
            try:
                self.through.objects.get_or_create(
                    tag=tag, **self._lookup_kwargs())
            except Exception as e:
                logger.exception(e)


class Thesaurus(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """
    identifier = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True)

    # read from the RDF file
    title = models.CharField(max_length=255, null=False, blank=False)
    # read from the RDF file
    date = models.CharField(max_length=20, default='')
    # read from the RDF file
    description = models.TextField(max_length=255, default='')

    slug = models.CharField(max_length=64, default='')

    def __str__(self):
        return "{0}".format(self.identifier)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Thesauri'


class ThesaurusKeywordLabel(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """

    # read from the RDF file
    lang = models.CharField(max_length=3)
    # read from the RDF file
    label = models.CharField(max_length=255)
    # note  = models.CharField(max_length=511)

    keyword = models.ForeignKey('ThesaurusKeyword', related_name='keyword', on_delete=models.CASCADE)

    def __str__(self):
        return "{0}".format(self.label)

    class Meta:
        ordering = ("keyword", "lang")
        verbose_name_plural = 'Labels'
        unique_together = (("keyword", "lang"),)


class ThesaurusKeyword(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """
    # read from the RDF file
    about = models.CharField(max_length=255, null=True, blank=True)
    # read from the RDF file
    alt_label = models.CharField(
        max_length=255,
        default='',
        null=True,
        blank=True)

    thesaurus = models.ForeignKey('Thesaurus', related_name='thesaurus', on_delete=models.CASCADE)

    def __str__(self):
        return "{0}".format(self.alt_label)

    @property
    def labels(self):
        return ThesaurusKeywordLabel.objects.filter(keyword=self)

    class Meta:
        ordering = ("alt_label",)
        verbose_name_plural = 'Thesaurus Keywords'
        unique_together = (("thesaurus", "alt_label"),)


class TaggedContentItem(ItemBase):
    content_object = models.ForeignKey('ResourceBase', on_delete=models.CASCADE)
    tag = models.ForeignKey('HierarchicalKeyword', related_name='keywords', on_delete=models.CASCADE)

    # see https://github.com/alex/django-taggit/issues/101
    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return cls.tag_model().objects.filter(**{
                '%s__content_object' % cls.tag_relname(): instance
            })
        return cls.tag_model().objects.filter(**{
            '%s__content_object__isnull' % cls.tag_relname(): False
        }).distinct()


class Region(MPTTModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children')

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images
    # and metadata records.
    bbox_x0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_x1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    srid = models.CharField(
        max_length=30,
        blank=False,
        null=False,
        default='EPSG:4326')

    def __str__(self):
        return "{0}".format(self.name)

    @property
    def bbox(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return [
            self.bbox_x0,
            self.bbox_x1,
            self.bbox_y0,
            self.bbox_y1,
            self.srid]

    @property
    def bbox_string(self):
        """BBOX is in the format: [x0,y0,x1,y1]."""
        return ",".join([str(self.bbox_x0), str(self.bbox_y0),
                         str(self.bbox_x1), str(self.bbox_y1)])

    class Meta:
        ordering = ("name",)
        verbose_name_plural = 'Metadata Regions'

    class MPTTMeta:
        order_insertion_by = ['name']


class RestrictionCodeType(models.Model):
    """
    Metadata information about the spatial representation type.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_RestrictionCode">
    """
    identifier = models.CharField(max_length=255, editable=False)
    description = models.TextField(max_length=255, editable=False)
    gn_description = models.TextField('GeoNode description', max_length=255)
    is_choice = models.BooleanField(default=True)

    def __str__(self):
        return "{0}".format(self.gn_description)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Metadata Restriction Code Types'


class License(models.Model):
    identifier = models.CharField(max_length=255, editable=False)
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    license_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{0}".format(self.name)

    @property
    def name_long(self):
        if self.abbreviation is None or len(self.abbreviation) == 0:
            return self.name
        else:
            return self.name + " (" + self.abbreviation + ")"

    @property
    def description_bullets(self):
        if self.description is None or len(self.description) == 0:
            return ""
        else:
            bullets = []
            lines = self.description.split("\n")
            for line in lines:
                bullets.append("+ " + line)
            return bullets

    class Meta:
        ordering = ("name",)
        verbose_name_plural = 'Licenses'


class ResourceBase(PolymorphicModel, ItemBase):
    """
    Base Resource Object loosely based on ISO 19115:2003
    """
    BASE_PERMISSIONS = {
        'read': ['view_resourcebase'],
        'write': [
            'change_resourcebase_metadata'
        ],
        'download': ['download_resourcebase'],
        'owner': [
            'change_resourcebase',
            'delete_resourcebase',
            'change_resourcebase_permissions',
            'publish_resourcebase'
        ]
    }

    PERMISSIONS = {}

    VALID_DATE_TYPES = [(x.lower(), _(x))
                        for x in ['Creation', 'Publication', 'Revision']]

    date_help_text = _('reference date for the cited resource')
    date_type_help_text = _('identification of when a given event occurred')
    edition_help_text = _('version of the cited resource')
    abstract_help_text = _(
        'brief narrative summary of the content of the resource(s)')
    purpose_help_text = _(
        'summary of the intentions with which the resource(s) was developed')
    maintenance_frequency_help_text = _(
        'frequency with which modifications and deletions are made to the data after '
        'it is first produced')
    keywords_help_text = _(
        'commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject '
        '(space or comma-separated)')
    tkeywords_help_text = _(
        'formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject '
        '(space or comma-separated)')
    regions_help_text = _('keyword identifies a location')
    restriction_code_type_help_text = _(
        'limitation(s) placed upon the access or use of the data.')
    constraints_other_help_text = _(
        'other restrictions and legal prerequisites for accessing and using the resource or'
        ' metadata')
    license_help_text = _('license of the dataset')
    language_help_text = _('language used within the dataset')
    category_help_text = _(
        'high-level geographic data thematic classification to assist in the grouping and search of '
        'available geographic data sets.')
    spatial_representation_type_help_text = _(
        'method used to represent geographic information in the dataset.')
    temporal_extent_start_help_text = _(
        'time period covered by the content of the dataset (start)')
    temporal_extent_end_help_text = _(
        'time period covered by the content of the dataset (end)')
    data_quality_statement_help_text = _(
        'general explanation of the data producer\'s knowledge about the lineage of a'
        ' dataset')
    doi_help_text = _(
        'a DOI will be added by Admin before publication.')
    doi = models.CharField(
        _('DOI'),
        max_length=255,
        blank=True,
        null=True,
        help_text=doi_help_text)
    attribution_help_text = _(
        'authority or function assigned, as to a ruler, legislative assembly, delegate, or the like.')
    attribution = models.CharField(
        _('Attribution'),
        max_length=2048,
        blank=True,
        null=True,
        help_text=attribution_help_text)
    # internal fields
    uuid = models.CharField(max_length=36)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name='owned_resource',
        verbose_name=_("Owner"),
        on_delete=models.CASCADE)
    contacts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ContactRole')
    title = models.CharField(_('title'), max_length=255, help_text=_(
        'name by which the cited resource is known'))
    alternate = models.CharField(max_length=128, null=True, blank=True)
    date = models.DateTimeField(
        _('date'),
        default=now,
        help_text=date_help_text)
    date_type = models.CharField(
        _('date type'),
        max_length=255,
        choices=VALID_DATE_TYPES,
        default='publication',
        help_text=date_type_help_text)
    edition = models.CharField(
        _('edition'),
        max_length=255,
        blank=True,
        null=True,
        help_text=edition_help_text)
    abstract = models.TextField(
        _('abstract'),
        max_length=2000,
        blank=True,
        help_text=abstract_help_text)
    purpose = models.TextField(
        _('purpose'),
        max_length=500,
        null=True,
        blank=True,
        help_text=purpose_help_text)
    maintenance_frequency = models.CharField(
        _('maintenance frequency'),
        max_length=255,
        choices=UPDATE_FREQUENCIES,
        blank=True,
        null=True,
        help_text=maintenance_frequency_help_text)
    keywords = TaggableManager(
        _('keywords'),
        through=TaggedContentItem,
        blank=True,
        help_text=keywords_help_text,
        manager=_HierarchicalTagManager)
    tkeywords = models.ManyToManyField(
        ThesaurusKeyword,
        verbose_name=_('keywords'),
        null=True,
        blank=True,
        help_text=tkeywords_help_text)
    regions = models.ManyToManyField(
        Region,
        verbose_name=_('keywords region'),
        null=True,
        blank=True,
        help_text=regions_help_text)
    restriction_code_type = models.ForeignKey(
        RestrictionCodeType,
        verbose_name=_('restrictions'),
        help_text=restriction_code_type_help_text,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_choice=True))
    constraints_other = models.TextField(
        _('restrictions other'),
        blank=True,
        null=True,
        help_text=constraints_other_help_text)
    license = models.ForeignKey(
        License,
        null=True,
        blank=True,
        verbose_name=_("License"),
        help_text=license_help_text,
        on_delete=models.SET_NULL)
    language = models.CharField(
        _('language'),
        max_length=3,
        choices=ALL_LANGUAGES,
        default='eng',
        help_text=language_help_text)
    category = models.ForeignKey(
        TopicCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_choice=True),
        help_text=category_help_text)
    spatial_representation_type = models.ForeignKey(
        SpatialRepresentationType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_choice=True),
        verbose_name=_("spatial representation type"),
        help_text=spatial_representation_type_help_text)

    # Section 5
    temporal_extent_start = models.DateTimeField(
        _('temporal extent start'),
        blank=True,
        null=True,
        help_text=temporal_extent_start_help_text)
    temporal_extent_end = models.DateTimeField(
        _('temporal extent end'),
        blank=True,
        null=True,
        help_text=temporal_extent_end_help_text)
    supplemental_information = models.TextField(
        _('supplemental information'),
        max_length=2000,
        default=DEFAULT_SUPPLEMENTAL_INFORMATION,
        help_text=_('any other descriptive information about the dataset'))

    # Section 8
    data_quality_statement = models.TextField(
        _('data quality statement'),
        max_length=2000,
        blank=True,
        null=True,
        help_text=data_quality_statement_help_text)
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    # Section 9
    # see metadata_author property definition below

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images
    # and metadata records.
    bbox_x0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_x1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    srid = models.CharField(
        max_length=30,
        blank=False,
        null=False,
        default='EPSG:4326')

    # CSW specific fields
    csw_typename = models.CharField(
        _('CSW typename'),
        max_length=32,
        default='gmd:MD_Metadata',
        null=False)
    csw_schema = models.CharField(
        _('CSW schema'),
        max_length=64,
        default='http://www.isotc211.org/2005/gmd',
        null=False)
    csw_mdsource = models.CharField(
        _('CSW source'),
        max_length=256,
        default='local',
        null=False)
    csw_insert_date = models.DateTimeField(
        _('CSW insert date'), auto_now_add=True, null=True)
    csw_type = models.CharField(
        _('CSW type'),
        max_length=32,
        default='dataset',
        null=False,
        choices=HIERARCHY_LEVELS)
    csw_anytext = models.TextField(_('CSW anytext'), null=True, blank=True)
    csw_wkt_geometry = models.TextField(
        _('CSW WKT geometry'),
        null=False,
        default='POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))')

    # metadata XML specific fields
    metadata_uploaded = models.BooleanField(default=False)
    metadata_uploaded_preserve = models.BooleanField(_('Metadata uploaded preserve'), default=False)
    metadata_xml = models.TextField(
        null=True,
        default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>',
        blank=True)
    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    featured = models.BooleanField(_("Featured"), default=False, help_text=_(
        'Should this resource be advertised in home page?'))
    is_published = models.BooleanField(
        _("Is Published"),
        default=True,
        help_text=_('Should this resource be published and searchable?'))
    is_approved = models.BooleanField(
        _("Approved"),
        default=True,
        help_text=_('Is this resource validated from a publisher or editor?'))

    # fields necessary for the apis
    thumbnail_url = models.TextField(_("Thumbnail url"), null=True, blank=True)
    detail_url = models.CharField(max_length=255, null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    # fields controlling security state
    dirty_state = models.BooleanField(
        _("Dirty State"),
        default=False,
        help_text=_('Security Rules Are Not Synched with GeoServer!'))

    users_geolimits = models.ManyToManyField(
        "UserGeoLimit",
        related_name="users_geolimits",
        null=True,
        blank=True)

    groups_geolimits = models.ManyToManyField(
        "GroupGeoLimit",
        related_name="groups_geolimits",
        null=True,
        blank=True)

    __is_approved = False
    __is_published = False

    objects = ResourceBaseManager()

    class Meta:
        # custom permissions,
        # add, change and delete are standard in django-guardian
        permissions = (
            # ('view_resourcebase', 'Can view resource'),
            ('change_resourcebase_permissions', 'Can change resource permissions'),
            ('download_resourcebase', 'Can download resource'),
            ('publish_resourcebase', 'Can publish resource'),
            ('change_resourcebase_metadata', 'Can change resource metadata'),
        )

    def __init__(self, *args, **kwargs):
        super(ResourceBase, self).__init__(*args, **kwargs)

    def __str__(self):
        return "{0}".format(self.title)

    def _remove_html_tags(self, attribute_str):
        pattern = re.compile('<.*?>')
        return re.sub(pattern, '', attribute_str)

    @property
    def raw_abstract(self):
        return self._remove_html_tags(self.abstract)

    @property
    def raw_purpose(self):
        return self._remove_html_tags(self.purpose)

    @property
    def raw_constraints_other(self):
        return self._remove_html_tags(self.constraints_other)

    @property
    def raw_supplemental_information(self):
        return self._remove_html_tags(self.supplemental_information)

    @property
    def raw_data_quality_statement(self):
        return self._remove_html_tags(self.data_quality_statement)

    def save(self, notify=False, *args, **kwargs):
        """
        Send a notification when a resource is created or updated
        """
        if hasattr(self, 'class_name') and (self.pk is None or notify):
            if self.pk is None and self.title:
                # Resource Created

                notice_type_label = '%s_created' % self.class_name.lower()
                recipients = get_notification_recipients(notice_type_label, resource=self)
                send_notification(recipients, notice_type_label, {'resource': self})
            elif self.pk:
                # Resource Updated
                _notification_sent = False

                # Approval Notifications Here
                if not _notification_sent and settings.ADMIN_MODERATE_UPLOADS:
                    if not self.__is_approved and self.is_approved:
                        # Set "approved" workflow permissions
                        self.set_workflow_perms(approved=True)

                        # Send "approved" notification
                        notice_type_label = '%s_approved' % self.class_name.lower()
                        recipients = get_notification_recipients(notice_type_label, resource=self)
                        send_notification(recipients, notice_type_label, {'resource': self})
                        _notification_sent = True

                # Publishing Notifications Here
                if not _notification_sent and settings.RESOURCE_PUBLISHING:
                    if not self.__is_published and self.is_published:
                        # Set "published" workflow permissions
                        self.set_workflow_perms(published=True)

                        # Send "published" notification
                        notice_type_label = '%s_published' % self.class_name.lower()
                        recipients = get_notification_recipients(notice_type_label, resource=self)
                        send_notification(recipients, notice_type_label, {'resource': self})
                        _notification_sent = True

                # Updated Notifications Here
                if not _notification_sent:
                    notice_type_label = '%s_updated' % self.class_name.lower()
                    recipients = get_notification_recipients(notice_type_label, resource=self)
                    send_notification(recipients, notice_type_label, {'resource': self})

        super(ResourceBase, self).save(*args, **kwargs)
        self.__is_approved = self.is_approved
        self.__is_published = self.is_published

    def delete(self, notify=True, *args, **kwargs):
        """
        Send a notification when a layer, map or document is deleted
        """
        if hasattr(self, 'class_name') and notify:
            notice_type_label = '%s_deleted' % self.class_name.lower()
            recipients = get_notification_recipients(notice_type_label, resource=self)
            send_notification(recipients, notice_type_label, {'resource': self})

        super(ResourceBase, self).delete(*args, **kwargs)


class UserGeoLimit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        on_delete=models.CASCADE)
    resource = models.ForeignKey(
        ResourceBase,
        null=False,
        blank=False,
        on_delete=models.CASCADE)
    wkt = models.TextField(
        db_column='wkt',
        blank=True)


class GroupGeoLimit(models.Model):
    group = models.ForeignKey(
        GroupProfile,
        null=False,
        blank=False,
        on_delete=models.CASCADE)
    resource = models.ForeignKey(
        ResourceBase,
        null=False,
        blank=False,
        on_delete=models.CASCADE)
    wkt = models.TextField(
        db_column='wkt',
        blank=True)
