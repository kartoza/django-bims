import requests
from bims.models import (
    BiologicalCollectionRecord,
    Dataset
)


def get_dataset_details_from_gbif(dataset_uuid):
    url = f'https://api.gbif.org/v1/dataset/{dataset_uuid}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        dataset_info = response.json()

        dataset_details = {
            'title': dataset_info.get('title', ''),
            'description': dataset_info.get('description', ''),
            'citation': dataset_info.get('citation', {}).get('text', ''),
            'url': dataset_info.get(
                'doi',
                f'https://www.gbif.org/dataset/{dataset_uuid}'),
        }
        return dataset_details
    except requests.exceptions.RequestException as e:
        print(f"Error fetching dataset details from GBIF: {e}")
        return None


def extract_dataset_keys():
    bio = BiologicalCollectionRecord.objects.filter(
        source_collection='gbif'
    )
    bio_with_dataset_keys = bio.exclude(
        additional_data__datasetKey__isnull=True
    ).distinct(
        'additional_data__datasetKey'
    )
    for bio_dataset in bio_with_dataset_keys:
        dataset_key = bio_dataset.additional_data['datasetKey']

        dataset = Dataset.objects.filter(uuid=dataset_key).first()
        if dataset and dataset.name and dataset.description and dataset.citation and dataset.url:
            print(
                f'Dataset {dataset_key} already exists '
                f'with complete information: {dataset.name}')
            continue

        dataset_details = get_dataset_details_from_gbif(dataset_key)

        dataset_name = dataset_details.get('title', '')
        description = dataset_details.get('description', '')
        citation = dataset_details.get('citation', '')
        url = dataset_details.get('url', '')

        dataset, created = Dataset.objects.update_or_create(
            uuid=dataset_key,
            defaults={
                'name': dataset_name,
                'description': description,
                'citation': citation,
                'url': url,
            }
        )
        print(f'{dataset_key} - {dataset_name} - {created}')
