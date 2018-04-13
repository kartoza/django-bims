from django.core.management import call_command
from celery import shared_task


@shared_task(name='tasks.update_fish_collection_record')
def update_fish_collection_record():
    call_command('update_fish_collection_record')
