# coding=utf-8
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.add_taxa_attribute', queue='update')
def add_taxa_attribute(taxon_extra_attribute_id):
    from bims.models.taxon_extra_attribute import TaxonExtraAttribute
    logger.info(
        'Updating ID : {}'.format(
        taxon_extra_attribute_id))
    try:
        taxon_extra_attribute = TaxonExtraAttribute.objects.get(
            id=taxon_extra_attribute_id
        )
    except TaxonExtraAttribute.DoesNotExist:
        logger.info(
            'Taxon attribute does not exist'
        )
        return

    taxon_group = taxon_extra_attribute.taxon_group
    taxa = taxon_group.taxonomies.all()
    logger.info(
        'Updating {} taxa'.format(
        taxa.count()))

    for taxon in taxa:
        if not taxon.additional_data:
            additional_data = {}
        else:
            additional_data = taxon.additional_data
        if taxon_extra_attribute.name not in additional_data:
            additional_data[taxon_extra_attribute.name] = ''
            taxon.additional_data = additional_data
            taxon.save()


@shared_task(name='bims.tasks.remove_taxa_attribute', queue='update')
def remove_taxa_attribute(taxon_extra_attribute_id):
    from bims.models.taxon_extra_attribute import TaxonExtraAttribute
    logger.info(
        'Updating ID : {}'.format(
            taxon_extra_attribute_id))
    try:
        taxon_extra_attribute = TaxonExtraAttribute.objects.get(
            id=taxon_extra_attribute_id
        )
    except TaxonExtraAttribute.DoesNotExist:
        return

    taxon_group = taxon_extra_attribute.taxon_group
    taxa = taxon_group.taxonomies.all()

    logger.info(
        'Updating {} taxa'.format(
        taxa.count()))

    for taxon in taxa:
        if taxon.additional_data and taxon_extra_attribute.name in taxon.additional_data:
            if taxon.additional_data[taxon_extra_attribute.name] == '':
                additional_data = taxon.additional_data
                del additional_data[taxon_extra_attribute.name]
                taxon.additional_data = additional_data
                taxon.save()