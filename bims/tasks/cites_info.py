from celery import shared_task



@shared_task(
    name='bims.tasks.fetch_and_save_cites_listing',
    queue='update',
    ignore_result=True)
def fetch_and_save_cites_listing(ids):
    from bims.models import (
        Taxonomy, CITESListingInfo)
    from bims.views.cites import get_cites_listing_data

    taxa = Taxonomy.objects.filter(id__in=ids)
    for taxonomy in taxa:
        if hasattr(taxonomy, 'taxonomyupdateproposal'):
            print('Taxonomy is a proposal')
            continue
        success, data = get_cites_listing_data(
            taxonomy.canonical_name)
        if success:
            for listing in data['cites_listing_info']:
                annotation = (
                    listing['annotation'] if listing['annotation'] else '-'
                )
                if not listing['appendix']:
                    continue
                print(listing)
                if not CITESListingInfo.objects.filter(
                    appendix=listing['appendix'],
                    annotation=annotation,
                    effective_at=listing['effective_at'],
                    taxonomy=taxonomy
                ).exists():
                    CITESListingInfo.objects.create(
                        appendix=listing['appendix'],
                        annotation=annotation,
                        effective_at=listing['effective_at'],
                        taxonomy=taxonomy
                    )
