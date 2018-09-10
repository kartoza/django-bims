from django.db.models import Count
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord


def get_landing_page_summary():
    taxon_class = 'taxon_gbif_id__taxon_class'
    category = 'category'
    summaries = BiologicalCollectionRecord.objects.values(
        taxon_class,
        category,
    ).annotate(
        total=Count(taxon_class),
        total_category=Count(category)
    )

    summary_data = {}

    for summary in summaries:
        class_name = summary[taxon_class]
        if not class_name:
            continue
        if class_name not in summary_data:
            summary_data[class_name] = {
                'total': 0
            }
        summary_data[class_name]['total'] += summary['total']
        summary_data[class_name][summary[category]] = \
            summary['total_category']

    return summary_data
