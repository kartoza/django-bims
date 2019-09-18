# coding=utf-8
"""
    Source reference that overridden with it's own source
"""

from collections import OrderedDict
from django.db import models
from django.conf import settings
from polymorphic.models import PolymorphicModel
from td_biblio.models.bibliography import Entry
from geonode.documents.models import Document


class SourceIsNotFound(Exception):
    """ Exception if source is not found"""

    def __init__(self):
        message = 'Source is not found'
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
        name = '%s' % self.name
        if self.url:
            name += ' (%s)' % self.url
        return u'%s' % name


class SourceReference(PolymorphicModel):
    """ Source reference model """
    note = models.TextField(
        null=True, blank=True)

    @property
    def reference_type(self):
        return 'Unpublished data'

    def link_template(self):
        """Returns html template containing the reference data"""
        if self.note:
            return (
                '<i class="fa fa-file-o" aria-hidden="true"></i>'
                ' {note}'.format(note=self.note)
            )
        return (
            '<i class="fa fa-file-o" aria-hidden="true"></i>'
            ' Unpublished data'
        )

    @property
    def source(self):
        return self

    def __unicode__(self):
        if not self.get_source_unicode():
            if self.note:
                return self.note
            else:
                return 'None'
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
        model_fields = {
            'note': note
        }
        if source:
            model_fields['source'] = source
        source_reference, created = _SourceModel.objects.get_or_create(
            **model_fields
        )
        return source_reference


class SourceReferenceBibliography(SourceReference):
    """ Source reference with bibliography source"""
    source = models.ForeignKey(Entry)

    @property
    def reference_type(self):
        return 'Peer-reviewed scientific article'

    @property
    def is_bibliography(self):
        return True

    def link_template(self):
        """Returns html template containing the reference data"""
        return (
            '<i class="fa fa-newspaper-o" aria-hidden="true"></i>'
            ' <a href="http://dx.doi.org/{doi}" '
            'target="_blank">{source}</a>'.format(
                doi=self.source.doi,
                source=self.source
            )
        )

    def __unicode__(self):
        return u'%s' % self.source


class SourceReferenceDatabase(SourceReference):
    """ Source reference with database source"""
    source = models.ForeignKey(DatabaseRecord)

    @property
    def reference_type(self):
        return 'Database'

    def link_template(self):
        """Returns html template containing the reference data"""
        if self.source.url:
            return (
                '<i class="fa fa-database" aria-hidden="true"></i>'
                ' <a href="{url}" '
                'target="_blank">{source}</a>'.format(
                    url=self.source.url,
                    source=self.source
                )
            )
        return (
            '<i class="fa fa-database" aria-hidden="true"></i>'
            ' {source}'.format(
                source=self.source
            )
        )

    def __unicode__(self):
        return u'%s' % self.source


class SourceReferenceDocument(SourceReference):
    """ Source reference with database source"""
    source = models.ForeignKey(Document)

    def link_template(self):
        """Returns html template containing the reference data"""
        return (
            '<i class="fa fa-file-pdf-o" aria-hidden="true"></i>'
            ' <a href="{media}{url}" '
            'download>{source}</a>'.format(
                media=settings.MEDIA_URL,
                url=self.source.doc_file,
                source=self.source
            )
        )

    @property
    def reference_type(self):
        return 'Published report or thesis'

    def __unicode__(self):
        return u'%s' % self.source


LIST_SOURCE_REFERENCES = OrderedDict([
    (SourceReferenceDatabase().reference_type, SourceReferenceDatabase),
    (
        SourceReferenceBibliography().reference_type,
        SourceReferenceBibliography),
    (SourceReferenceDocument().reference_type, SourceReferenceDocument),
    (SourceReference().reference_type, SourceReference),
])
