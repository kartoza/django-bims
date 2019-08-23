from django.contrib.gis.db import models
from geonode.documents.models import Document
from bims.utils.model import parsing_value_by_type


class BimsDocument(models.Model):
    """Data source for forms"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    author = models.CharField(max_length=512, null=True, blank=True)

    def __unicode__(self):
        return self.document.__unicode__()

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
