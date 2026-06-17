from django.db import transaction, IntegrityError
from django.db.models import ForeignKey
from django.apps import apps

from bims.models.location_site import LocationSite
from climate.models import Climate


def merge_climate_stations(primary_site, secondary_sites):
    """
    Merge secondary climate stations into primary_site.
    """
    secondary_pks = [s.pk for s in secondary_sites]

    with transaction.atomic():
        for secondary in secondary_sites:
            existing_dates = set(
                Climate.objects.filter(
                    location_site=primary_site
                ).values_list('date', flat=True)
            )
            Climate.objects.filter(
                location_site=secondary,
                date__in=existing_dates
            ).delete()
            Climate.objects.filter(
                location_site=secondary
            ).update(location_site=primary_site)

        for model in apps.get_models():
            if model == Climate:
                continue

            for field in model._meta.get_fields():
                if not isinstance(field, ForeignKey):
                    continue
                if getattr(field.remote_field, 'model', None) is not LocationSite:
                    continue

                site_field = field.name
                qs = model.objects.filter(**{f'{site_field}__in': secondary_pks})
                if not qs.exists():
                    continue

                try:
                    qs.update(**{site_field: primary_site})
                except IntegrityError:
                    for pk in qs.values_list('pk', flat=True):
                        try:
                            model.objects.filter(pk=pk).update(
                                **{site_field: primary_site}
                            )
                        except IntegrityError:
                            pass

        LocationSite.objects.filter(pk__in=secondary_pks).delete()
