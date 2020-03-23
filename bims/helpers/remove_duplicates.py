from django.db.models.fields.related import ForeignObjectRel


def remove_duplicates(queryset):
    """
    Remove duplicates, then update all references to original data.
    Return the original data.

    :param queryset: Queryset of duplicated data
    :return: single model data if duplicates found, else None
    """
    if not queryset.exists():
        return None
    if queryset.count() == 1:
        return queryset[0]

    original_data = queryset[0]

    links = [
        rel.get_accessor_name() for rel in original_data._meta.get_fields()
        if issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for duplicate in queryset[1:]:
            print('----- {} -----'.format(str(duplicate)))
            for link in links:
                try:
                    objects = getattr(duplicate, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for Model : {model}'.format(
                            obj=str(objects.model._meta.label),
                            model=str(duplicate)
                        ))
                        update_dict = {
                            getattr(duplicate, link).field.name: queryset
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            print(''.join(['-' for i in range(len(str(duplicate)) + 12)]))
    queryset.exclude(id=original_data.id).delete()
    return original_data
