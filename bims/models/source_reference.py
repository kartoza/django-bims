# coding=utf-8
"""
    Source reference that overridden with it's own source
"""

from django.db import models
from polymorphic.models import PolymorphicModel
from td_biblio.models.bibliography import Entry
from geonode.documents.models import Document


class SourceIsNotFound(Exception):
    """ Exception if source is not found"""

    def __init__(self):
        message = 'source is not found'
        errors = message
        super(SourceIsNotFound, self).__init__(message)
        self.errors = errors


class CategoryIsNotRecognized(Exception):
    """ If category is not recognized """

    def __init__(self):
        message = 'Category is not recognized'
        errors = message
        super(CategoryIsNotRecognized, self).__init__(message)
        self.errors = errors


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
        if not self.get_source_unicode() and self.note:
            return self.note
        else:
            return self.get_source_unicode()

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

    @staticmethod
    def create_source_reference(category, source_id, note):
        """ Create source reference based on category """
        source = None
        _SourceModel = None
        try:
            if category == 'bibliography':
                source = Entry.objects.get(id=source_id)
                _SourceModel = SourceReferenceBibliography
            elif category == 'document':
                source = Document.objects.get(id=source_id)
                _SourceModel = SourceReferenceDocument
            elif category == 'database':
                source = DatabaseRecord.objects.get(id=source_id)
                _SourceModel = SourceReferenceDatabase
            elif category:
                raise CategoryIsNotRecognized()
            else:
                _SourceModel = SourceReference
        except (
                Entry.DoesNotExist,
                Document.DoesNotExist,
                DatabaseRecord.DoesNotExist):
            raise SourceIsNotFound()
        source_reference = _SourceModel()
        source_reference.note = note
        if source:
            source_reference.source = source
        source_reference.save()
        return source_reference


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
