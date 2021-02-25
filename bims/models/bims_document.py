from django.contrib.gis.db import models
from django.conf import settings
from django.dispatch import receiver
from geonode.documents.models import Document
from bims.utils.model import parsing_value_by_type
from bims.utils.decorator import prevent_recursion


class BimsDocument(models.Model):
    """Data source for forms"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    author = models.CharField(max_length=512, null=True, blank=True)
    authors = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True,
        through='BimsDocumentAuthorship'
    )

    def __unicode__(self):
        return self.document.__unicode__()

    @property
    def authors_string(self):
        author_string = ''
        for author in self.authors.all():
            if author_string:
                author_string += ', '
            author_string += author.first_name + ' ' + author.last_name
        return author_string

    def update_metadata(self, data, silent=False):
        """ Update metadata to this object.
        :param data: data that will be updated
        :type data: dict
        """
        for field in BimsDocument._meta.get_fields():
            field = field.name
            if field in ['id', 'document']:
                continue
            try:
                value = parsing_value_by_type(self, field, data[field])
                if value:
                    setattr(self, field, value)
            except KeyError:
                pass
            except ValueError as e:
                if not silent:
                    raise e
        self.save()

    def save(self, *args, **kwargs):
        if self.document.metadata_author:
            self.author = self.document.metadata_author.get_full_name()
        if not self.year and self.document.date:
            self.year = self.document.date.year
        try:
            if not self.authors.all().exists():
                self.authors.add(self.document.owner)
        except ValueError:
            pass
        super(BimsDocument, self).save(*args, **kwargs)


class BimsDocumentAuthorship(models.Model):
    """Author model for bims document"""
    bimsdocument = models.ForeignKey(
        BimsDocument,
        on_delete=models.CASCADE,
        null=False,
    )
    profile = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ordering = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'bims_bimsdocument_authors'
        ordering = ('ordering', )


@receiver(models.signals.post_save, sender=BimsDocument)
@prevent_recursion
def bims_document_post_save_handler(sender, instance, **kwargs):
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
