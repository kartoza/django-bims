
from django.db.models.fields.reverse_related import ForeignObjectRel
from bims.utils.logger import log


def merge_sampling_method(excluded_sampling_method=None, sampling_methods=None):
    """
    Merge multiple sampling methods
    """
    if not excluded_sampling_method:
        return
    if not sampling_methods:
        return
    sampling_methods = sampling_methods.exclude(id=excluded_sampling_method.id)

    if sampling_methods.count() < 1:
        return

    log('Merging %s data' % sampling_methods.count())

    links = [
        rel.get_accessor_name() for rel in excluded_sampling_method._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for sampling_method in sampling_methods:
            log('----- {} -----'.format(str(sampling_method)))
            for link in links:
                try:
                    objects = getattr(sampling_method, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for : {sampling_method}'.format(
                            obj=str(objects.model._meta.label),
                            sampling_method=str(sampling_method)
                        ))
                        update_dict = {
                            getattr(
                                sampling_method, link
                            ).field.name: excluded_sampling_method
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            log(''.join(['-' for i in range(len(str(sampling_method)) + 12)]))

    sampling_methods.delete()
