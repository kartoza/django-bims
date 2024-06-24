# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db.models import signals
from django_tenants.utils import get_tenant_model, schema_context

from bims.models import (
    BiologicalCollectionRecord, collection_post_save_handler, IUCNStatus
)
from bims.utils.logger import log


class Command(BaseCommand):

    def create_or_update_iucn_status(self):
        categories = [
            {'category': 'EX', 'national': False, 'sensitive': False, 'colour': '#606060', 'order': 0},
            {'category': 'EW', 'national': False, 'sensitive': False, 'colour': '#808080', 'order': 1},
            {'category': 'CR', 'national': False, 'sensitive': True, 'colour': '#B00000', 'order': 2},
            {'category': 'EN', 'national': False, 'sensitive': True, 'colour': '#D00000', 'order': 3},
            {'category': 'VU', 'national': False, 'sensitive': True, 'colour': '#FF0000', 'order': 4},
            {'category': 'NT', 'national': False, 'sensitive': False, 'colour': '#FFC000', 'order': 5},
            {'category': 'LC', 'national': False, 'sensitive': False, 'colour': '#009106', 'order': 6},
            {'category': 'DD', 'national': False, 'sensitive': False, 'colour': '#808000', 'order': 7},
            {'category': 'NE', 'national': False, 'sensitive': False, 'colour': '#808000', 'order': 8},

            {'category': 'EX', 'national': True, 'sensitive': False, 'colour': '#606060', 'order': 9},
            {'category': 'EW', 'national': True, 'sensitive': False, 'colour': '#606060', 'order': 10},
            {'category': 'RE', 'national': True, 'sensitive': False, 'colour': '#404040', 'order': 11},
            {'category': 'CR PE', 'national': True, 'sensitive': True, 'colour': '#A00000', 'order': 12},
            {'category': 'EN', 'national': True, 'sensitive': True, 'colour': '#D00000', 'order': 13},
            {'category': 'VU', 'national': True, 'sensitive': True, 'colour': '#FF0000', 'order': 14},
            {'category': 'NT', 'national': True, 'sensitive': False, 'colour': '#FFC000', 'order': 15},
            {'category': 'CA', 'national': True, 'sensitive': False, 'colour': '#FFC000', 'order': 16},
            {'category': 'RA', 'national': True, 'sensitive': False, 'colour': '#FF8000', 'order': 17},
            {'category': 'D', 'national': True, 'sensitive': False, 'colour': '#FF4000', 'order': 18},
            {'category': 'DDD', 'national': True, 'sensitive': False, 'colour': '#808000', 'order': 19},
            {'category': 'DDT', 'national': True, 'sensitive': False, 'colour': '#808000', 'order': 20},
            {'category': 'LC', 'national': True, 'sensitive': False, 'colour': '#009106', 'order': 21},
        ]
        for cat in categories:
            iucn_status, created = IUCNStatus.objects.update_or_create(
                category=cat['category'], national=cat['national'],
                defaults={
                    'sensitive': cat['sensitive'],
                    'colour': cat['colour'],
                    'order': cat['order']
                }
            )
            if created:
                print(f'Created {cat["category"]} (national={cat["national"]})')
            else:
                print(f'Updated {cat["category"]} (national={cat["national"]})')

    def handle(self, *args, **options):

        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.all().exclude(schema_name='public')

        for tenant in tenants:
            with schema_context(tenant.schema_name):
                self.create_or_update_iucn_status()
