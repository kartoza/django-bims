# coding=utf-8
"""Record type model definition.

"""
from django.db import models
from django.db.models import ForeignObjectRel
from ordered_model.models import OrderedModel


class RecordType(OrderedModel):
    name = models.CharField(
        max_length=256,
    )

    is_hidden_in_form = models.BooleanField(
        help_text='Indicate if this record type'
                  ' should be hidden in forms.',
        default=False
    )

    verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


def merge_record_types(primary_record_type, record_type_list):
    """
    Merge multiple record types into one record_type
    """
    if not primary_record_type and not record_type_list:
        return

    print('Merging %s record type' % len(record_type_list))

    record_types = RecordType.objects.filter(
        id__in=record_type_list.values_list('id', flat=True)
    ).exclude(id=primary_record_type.id)

    links = [
        rel.get_accessor_name() for rel in primary_record_type._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for record_type in record_types:
            for link in links:
                try:
                    objects = getattr(record_type, link).all()
                    if objects.count() > 0:
                        update_dict = {
                            getattr(record_type, link).field.name: primary_record_type
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    print(e)
                    continue
            record_type.delete()
