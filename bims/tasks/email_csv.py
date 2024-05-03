import os
import csv
import zipfile

from celery import shared_task
from django.db import connection

from bims.utils.domain import get_current_domain


@shared_task(name='bims.tasks.email_csv', queue='search')
def send_csv_via_email(
        user_id,
        csv_file,
        file_name='OccurrenceData',
        approved=False,
        download_request_id=None):
    """
    Send an email to requesting user with csv file attached
    :param user_id: User id
    :param csv_file: Path of csv file
    :param file_name: Name of the file
    :param approved: Whether the request has been approved or not
    :param download_request_id: Id of the download request
    :return:
    """
    from preferences import preferences
    from django.contrib.sites.models import Site
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from bims.models.download_request import DownloadRequest

    user = get_user_model().objects.get(id=user_id)

    download_request = None
    extension = 'csv'
    download_file_path = csv_file

    if not approved and download_request_id:
        try:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
            download_request.request_category = file_name
            download_request.request_file = csv_file
            download_request.save()
        except DownloadRequest.DoesNotExist:
            pass

    email_template = 'csv_download/csv_created'
    if download_request and download_request.resource_type == DownloadRequest.XLS:
        import pandas as pd
        df = pd.read_csv(csv_file, encoding='ISO-8859-1', on_bad_lines='warn')
        excel_file_path = os.path.splitext(csv_file)[0] + '.xlsx'
        df.to_excel(excel_file_path, index=False)
        extension = 'xlsx'
        download_file_path = excel_file_path
        email_template = 'excel_download/excel_created'

    ctx = {
        'username': user.username,
        'current_site': get_current_domain(),
    }
    subject = render_to_string(
        '{0}_subject.txt'.format(email_template),
        ctx
    )
    message = render_to_string(
        '{}_message.txt'.format(email_template),
        ctx
    )
    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email])
    zip_folder = os.path.join(
        settings.MEDIA_ROOT, settings.PROCESSED_CSV_PATH, user.username)
    if not os.path.exists(zip_folder):
        os.mkdir(zip_folder)
    zip_file = os.path.join(zip_folder, '{}.zip'.format(file_name))
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(download_file_path, f'{file_name}.{extension}')
        if preferences.SiteSetting.readme_download:
            zf.write(
                preferences.SiteSetting.readme_download.path,
                os.path.basename(preferences.SiteSetting.readme_download.path)
            )
    msg.attach_file(zip_file, 'application/octet-stream')
    msg.content_subtype = 'html'
    msg.send()


@shared_task(name='bims.tasks.send_location_site_email', queue='search')
def send_location_site_email(location_site_id, user_id):
    """
    Send the new location site data to the user and staff.
    Create CSV from location site and attach it to email.
    """
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from django.core.mail import EmailMessage
    from bims.models.location_site import LocationSite

    user = get_user_model().objects.get(id=user_id)
    location_site = LocationSite.objects.get(id=location_site_id)

    current_site = get_current_domain()

    csv_data = [
        ["ID", "Site Code", "Ecosystem Type",
         "User Site Code",
         "River Name",
         "User River Name",
         "Wetland Name",
         "User Wetland Name",
         "Description", "Owner", "URL"],
        [location_site.id,
         location_site.site_code,
         location_site.ecosystem_type.capitalize(),
         location_site.legacy_site_code,
         location_site.river.name if location_site.river else '-',
         location_site.legacy_river_name,
         location_site.wetland_name,
         location_site.user_wetland_name,
         location_site.site_description,
         location_site.owner.username,
         'http://{url}/location-site-form/update/?id={id}'.format(
             url=current_site,
             id=location_site.id
         )
         ]]

    # Write CSV data to a file
    csv_file_name = f"location_site_{location_site.id}.csv"
    with open(csv_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)

    email_body = """
        You have received the following notice from {current_site}:
        
        A new location site has been submitted through the mobile app. 
        Details of the submission are attached in the CSV file.
        """.format(current_site=current_site)

    bcc_recipients = list(
        get_user_model().objects.filter(is_superuser=True).values_list('email', flat=True)
    )

    owner_email = user.email

    if owner_email in bcc_recipients:
        bcc_recipients.remove(owner_email)

    # Send an email with the attached CSV
    email = EmailMessage(
        '[{}] New Location Site Data Submission'.format(current_site),
        email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
        bcc=bcc_recipients
    )
    email.attach_file(csv_file_name)
    email.send()

    os.remove(csv_file_name)
