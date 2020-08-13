# coding=utf-8
"""
    Source reference that overridden with it's own source
"""
import re
from collections import OrderedDict
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
from td_biblio.models.bibliography import Entry
from geonode.documents.models import Document
from bims.helpers.remove_duplicates import remove_duplicates
from bims.utils.decorator import prevent_recursion
from bims.models.bims_document import BimsDocument


def format_authors(users):
    """Format queryset of users to readable format"""
    if not users:
        return ''
    index = 0
    author = u''
    for doc_author in users:
        if (0 < index <
                len(users) - 1):
            author += ', '
        elif index > 0 and index == len(users) - 1:
            author += ' & '
        author += u'{first_name} {last_name}'.format(
            first_name=doc_author.first_name,
            last_name=doc_author.last_name
        )
        index += 1
    return author


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

    def __str__(self):
        name = '%s' % self.name
        if self.url:
            name += ' (%s)' % self.url
        return '%s' % name


class SourceReference(PolymorphicModel):
    """ Source reference model """
    note = models.TextField(
        null=True, blank=True)
    source_name = models.CharField(
        blank=True,
        default='',
        max_length=512
    )

    @property
    def occurrences(self):
        from bims.models.biological_collection_record import (
            BiologicalCollectionRecord
        )
        return BiologicalCollectionRecord.objects.filter(
            source_reference=self.id
        ).count()

    @property
    def year(self):
        if re.search(r'[12]\d{3}', self.source_name):
            year = re.findall(r'[12]\d{3}', self.source_name)[0]
            return year
        return '-'

    @property
    def authors(self):
        return '-'

    @property
    def title(self):
        if self.source_name:
            return self.source_name
        else:
            return 'Unpublished data'

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

    def __str__(self):
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
        if not category:
            try:
                source_reference, _ = SourceReference.objects.get_or_create(
                    **model_fields)
            except SourceReference.MultipleObjectsReturned:
                source_reference = remove_duplicates(
                    SourceReference.objects.filter(
                        **model_fields
                    ))
            return source_reference
        try:
            source_reference, created = _SourceModel.objects.get_or_create(
                **model_fields
            )
        except _SourceModel.MultipleObjectsReturned:
            source_reference = _SourceModel.objects.filter(
                **model_fields
            )[0]
        return source_reference


class SourceReferenceBibliography(SourceReference):
    """ Source reference with bibliography source"""
    source = models.ForeignKey(Entry, null=True, on_delete=models.CASCADE)
    document = models.ForeignKey(
        Document, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def title(self):
        return self.source.title

    @property
    def authors(self):
        authors = None
        if self.document:
            try:
                bims_document = BimsDocument.objects.get(
                    document__id=self.document.id
                )
                if bims_document.authors.all().exists():
                    authors = bims_document.authors.all()
            except BimsDocument.DoesNotExist:
                pass
        if not authors:
            authors = self.source.get_authors()
        authors_name = format_authors(authors)
        return authors_name if authors_name else '-'

    @property
    def year(self):
        try:
            bims_document = BimsDocument.objects.get(
                document=self.document
            )
            if bims_document.year:
                return bims_document.year
        except BimsDocument.DoesNotExist:
            pass
        if self.source.publication_date:
            return self.source.publication_date.year
        return '-'

    @staticmethod
    def create_entry(author_string, journal, date):
        pass

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
                source=self.title
            )
        )

    def __unicode__(self):
        return u'%s' % self.source

    def __str__(self):
        return '%s' % self.source


class SourceReferenceDatabase(SourceReference):
    """ Source reference with database source"""
    source = models.ForeignKey(DatabaseRecord, on_delete=models.CASCADE)
    document = models.ForeignKey(
        Document, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def title(self):
        return self.source.name

    @property
    def reference_type(self):
        return 'Database'

    @property
    def authors(self):
        return '-'

    @property
    def year(self):
        if re.search(r'[12]\d{3}', self.source_name):
            year = re.findall(r'[12]\d{3}', self.source_name)[0]
            return year
        return '-'

    def link_template(self):
        """Returns html template containing the reference data"""
        if self.source.url:
            return (
                '<i class="fa fa-database" aria-hidden="true"></i>'
                ' <a href="{url}" '
                'target="_blank">{source}</a>'.format(
                    url=self.source.url,
                    source=self.title
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
    source = models.ForeignKey(Document, on_delete=models.CASCADE)

    @property
    def year(self):
        try:
            bims_doc = BimsDocument.objects.get(
                document=self.source
            )
            if bims_doc.year:
                return bims_doc.year
        except BimsDocument.DoesNotExist:
            pass
        if self.source.date:
            return self.source.date.year
        return '-'

    @property
    def title(self):
        return self.source.title

    @property
    def authors(self):
        try:
            bims_doc = BimsDocument.objects.get(
                document=self.source
            )
            authors = bims_doc.authors.all()
            if authors.exists():
                return format_authors(authors)
        except BimsDocument.DoesNotExist:
            pass
        return '%(first_name)s %(last_name)s' % {
            'first_name': self.source.owner.first_name,
            'last_name': self.source.owner.last_name
        }

    def link_template(self):
        """Returns html template containing the reference data"""
        href = ''
        if self.source.doc_file:
            href = '"{media}{url}" download'.format(
                media=settings.MEDIA_URL,
                url=self.source.doc_file,
            )
        elif self.source.doc_url:
            href = '"{url}" target="_blank"'.format(
                url=self.source.doc_url,
            )
        return (
            '<i class="fa fa-file-pdf-o" aria-hidden="true"></i>'
            ' <a href={href}>{source}</a>'.format(
                href=href,
                source=self.title
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


@receiver(models.signals.post_save, sender=SourceReferenceDatabase)
@receiver(models.signals.post_save, sender=SourceReferenceBibliography)
@receiver(models.signals.post_save, sender=SourceReference)
@receiver(models.signals.post_save, sender=SourceReferenceDocument)
@prevent_recursion
def source_reference_post_save_handler(sender, instance, **kwargs):
    from bims.tasks.source_reference import (
        generate_source_reference_filter,
        SOURCE_REFERENCE_FILTER_FILE
    )
    import os
    from django.conf import settings
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        SOURCE_REFERENCE_FILTER_FILE
    )
    generate_source_reference_filter.delay(file_path)
