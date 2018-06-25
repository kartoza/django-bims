__author__ = 'Alison Mukoma <alison@kartoza.com'
__copywrite__ = 'kartoza.com'

import os

from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from bims.models.taxon import Taxon
from bims.models.biological_collection_record import BiologicalCollectionRecord
def create_pdf(pathname, current_site):

    # initialising the PDF for drawing content on it
    page = canvas.Canvas(pathname, pagesize=landscape(A4))
    width, height = A4
    center = height * 0.5

    margin_left = 125
    margin_bottom = 220

    records = Taxon.objects.all()
    total_collection = records.count()

    biological_total = BiologicalCollectionRecord.objects.count()
    for record in records:
        name = record.common_name
        status = record.iucn_status

    # we start to draw staff on the PDF
    page.setFillColorRGB(0.1, 0.1, 0.1)
    page.setFont('Times-Roman', 18)

    logo = 'reports/static/img/logo.png'
    wildlife_logo = 'reports/static/img/collection/wildlife.png'
    biodiversity_logo = 'reports/static/img/collection/biodiversity.png'
    page.setFont('Times-Bold', 26)
    page.drawImage(
            logo, 370, 480, width = 100, height = 100,
            preserveAspectRatio = True, mask = 'auto')
    page.drawCentredString(center, 450, 'Ledet Report')

    page.setFont('Times-Roman', 16)
    page.setFont('Times-Roman', 16)
    page.drawCentredString(
		    center, 290, 'Species')

    page.drawImage(
            wildlife_logo, 120, 220, width = 50, height = 50,
            preserveAspectRatio = True, mask = 'auto')
    page.drawString(180,
                    230,
                    'Total Taxa collection: {0}'.format(total_collection))

    page.drawImage(
		    biodiversity_logo, 120, 150, width = 50, height = 50,
		    preserveAspectRatio = True, mask = 'auto')
    page.drawString(180,
                    160,
                    'Total Biodiversity records: {0}'.format(biological_total))




    # footer information.
    # page.setFont('Times-Roman', 14)
    # page.drawString(
    #     margin_left,
    #     margin_bottom - 10,
    #     'We are still adding staff to this report.')
    # page.setFont('Times-Roman', 8)

    # closing the PDF with content
    page.showPage()
    page.save()


def view_pdf(request, **kwargs):

    current_site = request.META['HTTP_HOST']

    filename = '{}.{}'.format('ledet_report', 'pdf')
    storage_folder = ('reports')
    pathname = \
        os.path.join(
            '/home/web/media', '{}/{}'.format(storage_folder, filename))
    found = os.path.exists(pathname)
    if found:
        with open(pathname, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = \
                'filename={}.pdf'.format('ledet_report')
            return response
    else:
        makepath = '/home/web/media/{}/'.format(storage_folder)
        if not os.path.exists(makepath):
            os.makedirs(makepath)

        create_pdf(pathname, current_site)
        with open(pathname, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = \
                'filename={}.pdf'.format('ledet_report')
            return response
