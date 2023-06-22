from typing import List

from django.core.management import BaseCommand
from django.db.models import Count, Value
from functools import reduce
from django.db.models import Q
from django.db.models import signals
from django.db.models.functions import Coalesce
from easyaudit.signals.model_signals import (
    post_delete,
    post_save,
    pre_save,
    m2m_changed
)


from bims.models import (
    Survey,
    BiologicalCollectionRecord, LocationSite
)


class Command(BaseCommand):

    specific_site = 'B8LETA-00002'

    def disconnect_signals(self):
        signals.post_save.disconnect(
            post_delete,
            dispatch_uid='easy_audit_signals_post_delete')
        signals.post_save.disconnect(
            post_save, dispatch_uid='easy_audit_signals_post_save')
        signals.pre_save.disconnect(
            pre_save, dispatch_uid='easy_audit_signals_pre_save')
        signals.m2m_changed.disconnect(
            m2m_changed, dispatch_uid='easy_audit_signals_m2m_changed')

    def connect_signals(self):
        signals.post_save.connect(
            post_delete,
            dispatch_uid='easy_audit_signals_post_delete')
        signals.post_save.connect(
            post_save, dispatch_uid='easy_audit_signals_post_save')
        signals.pre_save.connect(
            pre_save, dispatch_uid='easy_audit_signals_pre_save')
        signals.m2m_changed.connect(
            m2m_changed, dispatch_uid='easy_audit_signals_m2m_changed')

    def get_related_fields(self, model):
        return [
            f for f in model._meta.get_fields()
            if (
               f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
            ]

    def clear_empty_surveys(self):
        related_fields = self.get_related_fields(Survey)
        unreferenced_surveys_query = reduce(
            lambda q1, q2: q1 & q2,
            (Q(**{f'{field.name}__isnull': True}) for field in
             related_fields),
        )
        unreferenced_surveys = Survey.objects.filter(
            unreferenced_surveys_query)
        print(f'Empty surveys : {unreferenced_surveys.count()}')
        unreferenced_surveys.delete()

    def check_duplicates_in_depth(self, site_ids: List[int] = []) -> None:
        """
        Check for duplicates more thoroughly in a list of sites. This process can
        take more time. Duplicates are deleted, keeping one instance.

        :param site_ids: List of site ids to check for duplicates.
        """
        self.stdout.write(self.style.HTTP_INFO(
            'Starting thorough duplicate check for specific site'))

        location_sites = LocationSite.objects.filter(
            id__in=site_ids
        )

        for location_site in location_sites:
            self.stdout.write(
                self.style.SUCCESS(f'Found site with ID : {location_site.id}, '
                                   f'Site Code : {location_site.site_code}'))

            duplicate_entries = BiologicalCollectionRecord.objects.filter(
                site=location_site
            ).annotate(
                normalized_abundance_number=Coalesce('abundance_number',
                                                     Value(0.0))
            ).values(
                'taxonomy',
                'collection_date',
                'normalized_abundance_number'
            ).annotate(
                id_count=Count('id')
            ).exclude(
                notes__icontains='sass'
            ).filter(
                id_count__gt=1
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Found {duplicate_entries.count()} duplicate entries'))

            for duplicate in duplicate_entries:
                duplicate_records = BiologicalCollectionRecord.objects.annotate(
                    normalized_abundance_number=Coalesce('abundance_number', Value(0.0))
                ).filter(
                    taxonomy=duplicate['taxonomy'],
                    collection_date=duplicate['collection_date'],
                    normalized_abundance_number=duplicate['normalized_abundance_number'],
                )
                # First, get the records with owners.
                records_with_owners = duplicate_records.filter(owner__isnull=False)

                if records_with_owners.exists():
                    # If we have records with owners, check for source reference.
                    records_with_source_reference = records_with_owners.filter(
                        source_reference__isnull=False)

                    if records_with_source_reference.exists():
                        # If we have records with both owner and source reference, keep them and delete the rest.
                        records_to_delete = records_with_owners.exclude(
                            id__in=records_with_source_reference.values('id'))
                        records_to_keep = records_with_source_reference
                    else:
                        # If none of the records with owners have a source reference, keep them and delete the rest.
                        records_to_delete = duplicate_records.exclude(
                            id__in=records_with_owners.values('id'))
                        records_to_keep = records_with_owners
                else:
                    # If none of the records have an owner, keep one (the first one) and delete the rest.
                    records_to_delete = duplicate_records.exclude(
                        id=duplicate_records.first().id)
                    records_to_keep = BiologicalCollectionRecord.objects.filter(
                        id=duplicate_records.first().id)

                if records_to_keep.count() >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Keeping records with IDs: '
                            f'{list(records_to_keep.values_list("id", "abundance_number"))}'
                        )
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f'Deleting records with IDs: '
                            f'{list(records_to_delete.values_list("id", "abundance_number"))}'
                        )
                    )

                    if records_to_delete.count() > 0:
                       records_to_delete.delete()

    def handle(self, *args, **options):
        self.disconnect_signals()

        self.clear_empty_surveys()

        duplicate_collections = BiologicalCollectionRecord.objects.filter(
            sitevisittaxon__isnull=True
        ).exclude(
            owner__username__icontains='_vm',
        ).values(
            'taxonomy',
            'owner',
            'collection_date',
            'site',
            'module_group',
            'biotope',
            'specific_biotope',
            'substratum',
            'sampling_method',
            'abundance_number',
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1
        )

        print(f'Total GBIF Duplicates {duplicate_collections.count()}')

        for duplicate in duplicate_collections:
            duplicates = BiologicalCollectionRecord.objects.filter(
                sitevisittaxon__isnull=True
            ).filter(
                taxonomy=duplicate['taxonomy'],
                owner=duplicate['owner'],
                collection_date=duplicate['collection_date'],
                site=duplicate['site'],
                module_group=duplicate['module_group'],
                biotope=duplicate['biotope'],
                specific_biotope=duplicate['specific_biotope'],
                substratum=duplicate['substratum'],
                sampling_method=duplicate['sampling_method'],
                abundance_number=duplicate['abundance_number'],
            )
            survey_to_keep = duplicates.first()
            surveys_to_delete = duplicates.exclude(id=survey_to_keep.id)
            print(f'Delete {surveys_to_delete.count()}')
            surveys_to_delete.delete()

        duplicate_collections = BiologicalCollectionRecord.objects.filter(
            sitevisittaxon__isnull=True
        ).exclude(
            Q(owner__username__icontains='gbif') | Q(owner__username__icontains='_vm'),
        ).values(
            'taxonomy',
            'owner',
            'collection_date',
            'site',
            'module_group',
            'biotope',
            'specific_biotope',
            'substratum',
            'sampling_method',
            'abundance_number',
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1
        )
        print(f'Total non GBIF Duplicates {duplicate_collections.count()}')
        for duplicate in duplicate_collections:
            duplicates = BiologicalCollectionRecord.objects.filter(
                sitevisittaxon__isnull=True
            ).filter(
                taxonomy=duplicate['taxonomy'],
                owner=duplicate['owner'],
                collection_date=duplicate['collection_date'],
                site=duplicate['site'],
                module_group=duplicate['module_group'],
                biotope=duplicate['biotope'],
                specific_biotope=duplicate['specific_biotope'],
                substratum=duplicate['substratum'],
                sampling_method=duplicate['sampling_method'],
                abundance_number=duplicate['abundance_number'],
            )

            survey_to_keep = duplicates.first()
            if duplicates.exclude(
                source_reference__isnull=True
            ).exists():
                survey_to_keep = duplicates.exclude(
                    source_reference__isnull=True
                ).first()

            surveys_to_delete = duplicates.exclude(id=survey_to_keep.id)
            print(
                f'collection to keep {survey_to_keep.id} '
                f'collection to delete {list(surveys_to_delete.values_list("id"))}'
            )
            if survey_to_keep.survey:
                print(
                    f'survey to keep {survey_to_keep.survey.id} '
                    f'survey to delete {list(surveys_to_delete.values_list("survey__id").distinct("survey"))}'
                )
            surveys_to_delete.delete()

        all_sites = (
            list(LocationSite.objects.filter(
                biological_collection_record__source_collection__iexact='fbis'
            ).exclude(
                biological_collection_record__notes__icontains='sass'
            ).distinct().values_list('id', flat=True))
        )

        self.check_duplicates_in_depth(all_sites)

        self.clear_empty_surveys()
        self.connect_signals()
