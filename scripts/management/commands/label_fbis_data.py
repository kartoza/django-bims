# -*- coding: utf-8 -*-
import json
import os

from django.core.management.base import BaseCommand

from django.db.models import signals
from easyaudit.signals.model_signals import pre_save as easyaudit_presave
from bims.models import (
    BiologicalCollectionRecord,
    LocationSite,
    LocationContext,
    generate_site_code,
    location_site_post_save_handler
)
from core.settings.utils import absolute_path

from bims.utils.logger import log


class Command(BaseCommand):

    def fix_sites_multiple_ecosystem_type(self, ecosystem_type=''):
        signals.pre_save.disconnect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

        bio_data = BiologicalCollectionRecord.objects.filter(
            ecosystem_type=ecosystem_type
        )
        bio_sites = LocationSite.objects.filter(
            id__in=list(
                bio_data.values_list('site', flat=True).distinct())
        )
        log(
            f'{ecosystem_type} Sites {bio_sites.count()}'
        )

        ecosystem_types = list(
            bio_sites.values_list(
                'biological_collection_record__ecosystem_type',
                flat=True
            ).distinct()
        )

        for original_ecosystem_type in ecosystem_types:
            if original_ecosystem_type == ecosystem_type:
                continue
            ecosystem_sites = bio_sites.filter(
                biological_collection_record__ecosystem_type=original_ecosystem_type
            ).distinct()
            log(
                f'{original_ecosystem_type} FBIS Sites {ecosystem_sites.count()}'
            )
            for _ecosystem_site in ecosystem_sites:
                eco_bio = BiologicalCollectionRecord.objects.filter(
                    site=_ecosystem_site,
                ).exclude(
                    ecosystem_type=ecosystem_type
                ).first()
                if not eco_bio:
                    continue
                log(
                    f'Processing {_ecosystem_site}'
                )
                site_original_id = _ecosystem_site.id
                _ecosystem_site.pk = None
                _ecosystem_site.ecosystem_type = original_ecosystem_type
                _ecosystem_site.save()

                # Duplicate LocationContext data for the new site
                location_contexts = LocationContext.objects.filter(site_id=site_original_id)
                for context in location_contexts:
                    context.pk = None
                    context.site = _ecosystem_site
                    context.save()

                new_site_code, _ = generate_site_code(
                    _ecosystem_site,
                    river_name=_ecosystem_site.river.name if _ecosystem_site.river else ''
                )
                log(
                    f'New Site Code for {_ecosystem_site.id} = {new_site_code}'
                )
                _ecosystem_site.site_code = new_site_code
                _ecosystem_site.save()

                records_linked_to_site = bio_data.filter(
                    site_id=site_original_id
                )
                log(
                    f'Updating {original_ecosystem_type} records {records_linked_to_site.count()}'
                )
                records_linked_to_site.update(
                    site=_ecosystem_site)

        signals.pre_save.connect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

    def fix_sites_multiple_source_collections(self, source_collection='gbif', ecosystem_type=''):
        signals.pre_save.disconnect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

        gbif_data = BiologicalCollectionRecord.objects.filter(
            source_collection__iexact=source_collection
        )
        gbif_sites = LocationSite.objects.filter(
            id__in=list(gbif_data.values_list('site', flat=True))
        )
        log(
            f'{source_collection} Sites {gbif_sites.count()}'
        )

        # Check gbif sites that also fbis sites
        gbif_fbis_sites = gbif_sites.filter(
            biological_collection_record__source_collection='fbis'
        ).distinct()
        log(
            f'{source_collection} FBIS Sites {gbif_fbis_sites.count()}'
        )

        for gbif_site in gbif_fbis_sites:
            log(
                f'Processing {gbif_site}'
            )
            site_original_id = gbif_site.id
            gbif_site.pk = None
            gbif_site.ecosystem_type = ecosystem_type
            gbif_site.save()

            # Duplicate LocationContext data for the new site
            location_contexts = LocationContext.objects.filter(site_id=site_original_id)
            for context in location_contexts:
                context.pk = None
                context.site = gbif_site
                context.save()

            new_site_code, _ = generate_site_code(
                gbif_site,
                river_name=gbif_site.river.name if gbif_site.river else ''
            )
            log(
                f'New Site Code for {gbif_site.id} = {new_site_code}'
            )
            gbif_site.site_code = new_site_code
            gbif_site.save()

            gbif_records_linked_to_site = gbif_data.filter(
                site_id=site_original_id
            )

            log(
                f'Updating {source_collection} records {gbif_records_linked_to_site.count()}'
            )
            gbif_records_linked_to_site.update(
                site=gbif_site)

        LocationSite.objects.filter(
            id__in=list(gbif_data.values_list('site', flat=True))
        ).update(ecosystem_type='')

        signals.pre_save.connect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

    def handle(self, *args, **options):
        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite
        )
        self.fix_sites_multiple_source_collections(
            'gbif'
        )
        self.fix_sites_multiple_source_collections(
            'virtual_museum'
        )
        path = os.path.join(
            absolute_path('scripts', 'management', 'commands'),
            'waterbody_uuids.json'
        )

        # Set all fbis sites to river
        sites = LocationSite.objects.filter(
            biological_collection_record__source_collection='fbis'
        ).distinct()

        sites.update(ecosystem_type='River')

        with open(path) as json_file:
            LocationSite.objects.filter(
                ecosystem_type='Open waterbody'
            ).update(ecosystem_type='')

            uuids = json.load(json_file)
            uuids_without_hyphen = [uuid.replace('-', '') for uuid in uuids]
            uuids_to_check = uuids + uuids_without_hyphen

            # Reset data to river
            bios = (
                BiologicalCollectionRecord.objects.filter(
                    ecosystem_type='Open waterbody',
                    source_collection='fbis')
            )
            bios.update(ecosystem_type='River')

            bio = BiologicalCollectionRecord.objects.filter(
                uuid__in=uuids_to_check
            )
            bio.update(
                ecosystem_type='Open waterbody'
            )
            self.fix_sites_multiple_ecosystem_type(
                ecosystem_type='Open waterbody'
            )

            open_waterbody_site = LocationSite.objects.filter(
                id__in=list(
                    bio.values_list('site', flat=True).distinct())
            )
            open_waterbody_site.update(ecosystem_type='Open waterbody')
            log(
                open_waterbody_site.count()
            )
            log(
                LocationSite.objects.filter(
                    ecosystem_type='Open waterbody'
                ).count()
            )

        signals.post_save.connect(
            location_site_post_save_handler,
            sender=LocationSite
        )
