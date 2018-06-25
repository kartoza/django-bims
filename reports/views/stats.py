__author__ = 'Alison Mukoma <alison@kartoza.com'
__copywrite__ = 'kartoza.com'

import os

from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from bims.models.taxon import Taxon
from bims.models.biological_collection_record import BiologicalCollectionRecord


def create_pdf(pathname, current_site):

    # initialising the PDF for drawing content on it
    page = canvas.Canvas(pathname, pagesize=letter)
    width, height = A4
    center = height * 0.5

    margin_left = 125
    margin_bottom = 220

    taxa_records = Taxon.objects.all()
    species_total = taxa_records.count()

    biological_total = BiologicalCollectionRecord.objects.count()


    # we start to draw staff on the PDF
    page.setFillColorRGB(0.1, 0.1, 0.1)
    page.setFont('Times-Roman', 18)

    logo = 'reports/static/img/logo.png'
    wildlife_logo = 'reports/static/img/collection/wildlife.png'
    biodiversity_logo = 'reports/static/img/collection/biodiversity.png'
    page.setFont('Times-Bold', 16)
    page.drawImage(
            logo, 230, 650, width = 100, height = 100,
            preserveAspectRatio = True, mask = 'auto')
    page.drawString(235, 630, 'Ledet Report')

    page.setFillColorRGB(0.1, 0.1, 0.1)
    page.setFont('Times-Roman', 12)
    page.drawString(
            380, 600, 'Species Name')

    page.setFont('Times-Roman', 10)
    page.drawString(
            380, 580, 'Some fancy name')

    page.setFillColorRGB(0.1, 0.1, 0.1)
    page.setFont('Times-Roman', 12)
    page.drawString(
            520, 600, 'ICUN Status')

    page.setFont('Times-Roman', 10)
    page.drawString(
            520, 580, 'Available')



    page.drawImage(
            wildlife_logo, 90, 550, width = 30, height = 30,
            preserveAspectRatio = True, mask = 'auto')
    page.setFont('Times-Roman', 10)
    page.drawString(130,
                    560,
                    'Total Species collection: {0}'.format(species_total))


    page.drawImage(
		    biodiversity_logo, 90, 500, width = 30, height = 30,
		    preserveAspectRatio = True, mask = 'auto')
    page.setFont('Times-Roman', 10)
    page.drawString(130,
                    510,
                    'Total Biodiversity records: {0}'.format(biological_total))


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
