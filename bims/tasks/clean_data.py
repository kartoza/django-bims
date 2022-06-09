import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.clean_data', queue='update')
def clean_data():
    from bims.models.water_temperature import WaterTemperature
    from bims.models.endemism import Endemism
    from bims.models.taxonomy import Taxonomy

    water_temperatures_without_site = (
        WaterTemperature.objects.filter(
            location_site__isnull=True
        )
    )

    if water_temperatures_without_site.exists():
        logger.debug('Found {} water_temperature without site'.format(
            water_temperatures_without_site.count()
        ))
        water_temperatures_without_site.delete()

    # Fix endemism
    taxa_without_endemism = Taxonomy.objects.filter(
        endemism__isnull=True,
        additional_data__Endemism__isnull=False
    ).exclude(
        additional_data__Endemism=''
    )
    if not taxa_without_endemism.exists():
        return
    logger.debug('Found {} taxa without endemism'.format(
        taxa_without_endemism.count()
    ))
    for taxon in taxa_without_endemism:
        endemism_data = taxon.additional_data['Endemism']
        logger.debug('Updating {taxon} with {endemism}'.format(
            taxon=taxon.canonical_name,
            endemism=endemism_data
        ))
        endemism_obj, _ = Endemism.objects.get_or_create(
            name=endemism_data
        )
        taxon.endemism = endemism_obj
        taxon.save()
