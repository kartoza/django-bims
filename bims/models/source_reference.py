# coding=utf-8
"""
    Source reference that overridden with it's own source
"""

from django.db import models
from polymorphic.models import PolymorphicModel
from td_biblio.models.bibliography import Entry
from geonode.documents.models import Document


class DatabaseRecord(models.Model):
    """ Model that has database records """
    name = models.CharField(
        null=False,
        blank=False,
        max_length=256
    )
    description = models.TextField(
        null=True, blank=True)
    url = models.URLField(
        null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name


class SourceReference(PolymorphicModel):
    """ Source reference model """
    note = models.TextField(
        null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.id

    def get_source_unicode(self):
        try:
            return self.sourcereferencebibliography.__unicode__()
        except SourceReferenceBibliography.DoesNotExist:
            pass
        try:
            return self.sourcereferencedatabase.__unicode__()
        except SourceReferenceDatabase.DoesNotExist:
            pass
        try:
            return self.sourcereferencedocument.__unicode__()
        except SourceReferenceDocument.DoesNotExist:
            pass
        return None


class SourceReferenceBibliography(SourceReference):
    """ Source reference with bibliography source"""
    source = models.ForeignKey(Entry)

    def __unicode__(self):
        return u'%s' % self.source


class SourceReferenceDatabase(SourceReference):
    """ Source reference with database source"""
    source = models.ForeignKey(DatabaseRecord)

    def __unicode__(self):
        return u'%s' % self.source


class SourceReferenceDocument(SourceReference):
    """ Source reference with database source"""
    source = models.ForeignKey(Document)

    def __unicode__(self):
        return u'%s' % self.source
