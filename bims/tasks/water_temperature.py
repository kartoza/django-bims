import csv
import logging
import time
from datetime import datetime

from bims.models.upload_session import UploadSession
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware

from bims.models import (
    SourceReference, WaterTemperature, SiteImage
)
from bims.models.location_site import LocationSite
from celery import shared_task
WATER_TEMPERATURE_CACHE_KEY = 'key'

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.process_water_temperature_data', queue='update')
def process_water_temperature_data(
        upload_session_id, site_image_id, requester_id, post_data):
    start_time = time.time()
    owner_id = post_data.get('owner_id', '').strip()
    interval = post_data.get('interval')
    date_format = post_data.get('format')
    source_reference_id = post_data.get('source_reference', '')
    requester = get_user_model().objects.get(id=requester_id)
    first_date = None
    success_response = ''
    source_reference = None
    location_site = LocationSite.objects.get(
        pk=post_data.get('site-id', None)
    )

    if site_image_id:
        site_image = SiteImage.objects.get(id=site_image_id)
    else:
        site_image = None

    # If collector id exist then get the user object
    owner = None
    if owner_id:
        try:
            owner = get_user_model().objects.get(
                id=int(owner_id))
        except get_user_model().DoesNotExist:
            pass
    else:
        owner = requester

    if source_reference_id:
        try:
            source_reference = SourceReference.objects.get(
                id=source_reference_id
            )
        except SourceReference.DoesNotExist:
            pass


    is_daily = False
    new_data = []
    existing_data = []

    if float(interval) != 24:
        date_format = date_format + ' %H:%M'
    else:
        is_daily = True

    per_record_time = 0

    if upload_session_id and upload_session_id != 'undefined':
        try:
            upload_session = UploadSession.objects.get(
                id=upload_session_id
            )
        except UploadSession.DoesNotExist:
            logger.error('Upload session not found')
            return

        with open(upload_session.process_file.path) as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            data = list(reader)
            date_field = 'Date Time' if 'Date Time' in headers else 'Date'

            print('Checking existing data... {}'.format(
                time.time() - start_time))

            for temperature in data:

                per_record_time = time.time()
                if is_daily:
                    water_temp_value = temperature['Mean']
                else:
                    water_temp_value = temperature['Water temperature']

                date_string = temperature[date_field]
                if len(date_string.split(
                        ':')) > 2 and ':%S' not in date_format:
                    date_format += ':%S'  # Add second

                date_time = make_aware(
                    datetime.strptime(date_string, date_format)
                )

                if not first_date:
                    first_date = date_time

                water_data = {
                    'date_time': date_time,
                    'location_site': location_site,
                    'is_daily': is_daily
                }

                query = WaterTemperature.objects.raw(
                    'SELECT * FROM "bims_watertemperature" WHERE '
                    '("bims_watertemperature"."date_time" = \'{date}\' AND '
                    '"bims_watertemperature"."location_site_id" = {site_id}) '
                    'LIMIT 1'.format(
                        date=date_time,
                        site_id=location_site.id
                    )
                )

                try:
                    query = query[0]
                    is_data_exists = True
                except:  # noqa
                    query = None
                    is_data_exists = False

                water_data['value'] = water_temp_value
                water_data['is_daily'] = is_daily
                water_data['minimum'] = (
                    temperature['Minimum'] if is_daily else 0
                )
                water_data['maximum'] = (
                    temperature['Maximum'] if is_daily else 0
                )
                water_data['owner'] = owner
                water_data['uploader'] = requester
                water_data['source_reference'] = source_reference

                if is_data_exists:
                    if (
                            query.value != float(water_data['value']) or
                            query.minimum != int(water_data['minimum']) or
                            query.maximum != int(water_data['maximum'])
                    ):
                        query.value = water_data['value']
                        query.minimum = water_data['minimum']
                        query.maximum = water_data['maximum']
                        existing_data.append(query)
                else:
                    new_data.append(
                        WaterTemperature(**water_data)
                    )

                per_record_time = time.time() - per_record_time

            print('Time per record {}'.format(per_record_time))
            print('Done loop {}'.format(
                time.time() - start_time))
            if new_data:
                WaterTemperature.objects.bulk_create(
                    new_data
                )
                success_response += '{} data has been added. '.format(
                    len(new_data)
                )
            if existing_data:
                print('Updating existing data... {}'.format(
                    time.time() - start_time))
                WaterTemperature.objects.bulk_update(
                    existing_data,
                    ['value', 'minimum', 'maximum', 'owner'],
                    batch_size=100
                )
                success_response += '{} data has been updated.'.format(
                    len(existing_data)
                )
            print('Finished {}'.format(
                time.time() - start_time))
            # Check existing water temperature with
            # different source reference
            if source_reference:
                water_temperature_sr = WaterTemperature.objects.filter(
                    date_time__year=first_date.year
                ).exclude(
                    source_reference=source_reference
                )

                if water_temperature_sr.exists():
                    water_temperature_sr.update(
                        source_reference=source_reference
                    )
                    success_response += (
                        ' Source reference is updated. '
                    )

            if site_image and first_date:
                site_image.date = first_date
                site_image.notes = 'Upload session id = {}'.format(
                        upload_session_id)
                site_image.save()

            upload_session.processed = True

            if not success_response:
                success_response += 'No new data added or updated.'

            if site_image:
                success_response += '\n' + 'Site image has been uploaded'

            upload_session.success_notes = (
                success_response
            )
            upload_session.save()
