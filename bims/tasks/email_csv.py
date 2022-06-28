import os
import zipfile
from celery import shared_task


@shared_task(name='bims.tasks.email_csv', queue='search')
def send_csv_via_email(
        user_id,
        csv_file,
        file_name = 'OccurrenceData',
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

    if not approved:
        if preferences.SiteSetting.enable_download_request_approval:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
            download_request.request_category = file_name
            download_request.request_file = csv_file
            download_request.save()
            return
        else:
            pass

    email_template = 'csv_download/csv_created'
    ctx = {
        'username': user.username,
        'current_site': Site.objects.get_current(),
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
        zf.write(csv_file, '{}.csv'.format(file_name))
        if preferences.SiteSetting.readme_download:
            zf.write(
                preferences.SiteSetting.readme_download.path,
                os.path.basename(preferences.SiteSetting.readme_download.path)
            )
    msg.attach_file(zip_file, 'application/octet-stream')
    msg.content_subtype = 'html'
    msg.send()
