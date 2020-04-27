from django.core.management import BaseCommand
from django.db.models import signals
from django.db.models import Count
from django.db.models.fields.related import ForeignObjectRel
from bims.models import LocationSite, location_site_post_save_handler
from bims.utils.logger import log


class Command(BaseCommand):
    # Merge duplicated sites

    def handle(self, *args, **options):
        location_sites = LocationSite.objects.exclude(
            site_code__iregex=r'([A-Za-z0-9]){1,6}-([A-Za-z0-9]*)$'
        )

        duplicated_sites = LocationSite.objects.exclude(
            site_code=''
        ).values('site_code').annotate(
            count=Count('site_code')
        ).values('site_code', 'count').filter(
            count__gt=1
        ).order_by(
            'site_code'
        )

        signals.post_save.disconnect(
            location_site_post_save_handler
        )

        for site in duplicated_sites:
            log('Update : {}'.format(
                site['site_code']
            ))
            sites = LocationSite.objects.filter(
                site_code=site['site_code']
            )
            preferred_site = sites[0]
            site_desc = ''
            for p_site in sites:
                if not p_site.site_description:
                    continue
                if not site_desc:
                    site_desc = p_site.site_description
                else:
                    site_desc += ';' + p_site.site_description
            preferred_site.site_description = site_desc
            preferred_site.save()
            sites_to_delete = sites.exclude(id=preferred_site.id)
            links = [
                rel.get_accessor_name() for rel in
                preferred_site._meta.get_fields() if
                issubclass(type(rel), ForeignObjectRel)
            ]
            if links:
                for site_to_delete in sites_to_delete:
                    log('----- {} -----'.format(str(site_to_delete)))
                    for link in links:
                        try:
                            objects = getattr(site_to_delete, link).all()
                            if objects.count() > 0:
                                print('Updating {obj} for : {taxon}'.format(
                                    obj=str(objects.model._meta.label),
                                    taxon=str(site_to_delete)
                                ))
                                update_dict = {
                                    getattr(site_to_delete,
                                            link).field.name: preferred_site
                                }
                                objects.update(**update_dict)
                        except Exception as e:  # noqa
                            continue

            sites_to_delete.delete()
