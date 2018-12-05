from django.db.models import Count
from bims.models import (
    BiologicalCollectionRecord,
    Taxonomy,
)


def get_landing_page_summary():
    taxonomy_filter = 'taxonomy__id'
    category = 'category'
    summaries = BiologicalCollectionRecord.objects.values(
        taxonomy_filter,
        category,
    ).annotate(
        total=Count(taxonomy_filter),
        total_category=Count(category)
    )

    summary_data = {}

    for summary in summaries:
        taxonomy_id = summary[taxonomy_filter]
        if not taxonomy_id:
            continue

        taxonomy = Taxonomy.objects.get(id=taxonomy_id)
        if not taxonomy:
            continue

        class_name = taxonomy.class_name
        if not class_name:
            continue
        if class_name not in summary_data:
            summary_data[class_name] = {
                'total': 0
            }
        summary_data[class_name]['total'] += summary['total']
        summary_data[class_name][summary[category]] = (
            summary['total_category']
        )

    return summary_data
