from celery import shared_task


@shared_task(name='bims.tasks.retrieve_datasets_from_gbif', queue='geocontext')
def retrieve_datasets_from_gbif():
    from bims.scripts.extract_dataset_keys import extract_dataset_keys
    extract_dataset_keys()
