from django.core.management import BaseCommand
from django.db.models import Count
from functools import reduce
from django.db.models import Q
from django.db.models import signals
from easyaudit.signals.model_signals import (
    post_delete,
    post_save,
    pre_save,
    m2m_changed
)


from bims.models import (
    Survey,
    BiologicalCollectionRecord
)


class Command(BaseCommand):

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

        self.clear_empty_surveys()

        self.connect_signals()
