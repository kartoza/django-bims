from django.db.models.fields.reverse_related import ForeignObjectRel

from bims.utils.logger import log


def merge_endemism(excluded_endemism=None, endemisms=None):
    """
    Merge multiple endemism
    """

    if not excluded_endemism:
        return
    if not endemisms:
        return
    endemisms = endemisms.exclude(id=excluded_endemism.id)

    if endemisms.count() < 1:
        return

    log('Merging %s data' % endemisms.count())

    links = [
        rel.get_accessor_name() for rel in excluded_endemism._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for endemism in endemisms:
            log('----- {} -----'.format(str(endemism)))
            for link in links:
                try:
                    objects = getattr(endemism, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for : {endemism}'.format(
                            obj=str(objects.model._meta.label),
                            endemism=str(endemism)
                        ))
                        update_dict = {
                            getattr(
                                endemism, link
                            ).field.name: excluded_endemism
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            log(''.join(['-' for i in range(len(str(endemism)) + 12)]))

    endemisms.delete()
