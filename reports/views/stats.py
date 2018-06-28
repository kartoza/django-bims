__author__ = 'Alison Mukoma <alison@kartoza.com'
__copywrite__ = 'kartoza.com'

import os
from time import gmtime, strftime
import datetime

from django.http import HttpResponse

from reportlab.pdfgen import canvas

from reportlab.lib.colors import Color, yellowgreen,darkred, yellow, \
    greenyellow, \
    mediumseagreen
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter

from bims.models.taxon import Taxon
from bims.models.biological_collection_record import BiologicalCollectionRecord


def create_pdf(pathname, current_site):

    # initialising the PDF for drawing content on it
    page = canvas.Canvas(pathname, pagesize=letter)

    page.radialGradient(105*mm, 240*mm, 60*mm, (darkred, yellow,
                                                yellowgreen), (0, 0.8, 1))

    species_records = Taxon.objects.all()
    species_total = species_records.count()

    biological_total = BiologicalCollectionRecord.objects.count()


    # we start to draw staff on the PDF
    # page.setFillColorRGB(0.2, 0.2, 0.2)

    logo = 'reports/static/img/logo.png'
    wildlife_logo = 'reports/static/img/collection/wildlife.png'
    biodiversity_logo = 'reports/static/img/collection/biodiversity.png'
    page.setFont('Helvetica-Bold', 16)

    page.drawImage(
            logo, 250, 650, width = 100, height = 100,
            preserveAspectRatio = True, mask = 'auto')
    page.drawString(255, 630, 'Ledet Report')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(220,
                    600,
                    'Protected area management role')
    now = datetime.date.today()
    time = now.strftime('%d, %b %Y')

    page.setFont('Helvetica', 10)
    page.drawString(260,
                    580,
                    'Date: {}'.format(time))
    name_height = 530
    status_height = 530

    for specie in species_records:

        page.setFillColorRGB(0.1, 0.1, 0.1)
        page.setFont('Helvetica', 12)
        page.drawString(
                380, 550, 'Species Name')

        page.setFont('Helvetica', 10)
        page.drawString(
                380, name_height, specie.scientific_name)

        page.setFillColorRGB(0.1, 0.1, 0.1)
        page.setFont('Helvetica', 12)
        page.drawString(
                520, 550, 'IUCN Status')

        page.setFont('Helvetica', 10)
        page.drawString(
                520, status_height, 'Available')

        name_height -= 20
        status_height -= 20

    page.drawImage(
            wildlife_logo, 90, 550, width = 30, height = 30,
            preserveAspectRatio = True, mask = 'auto')
    page.setFont('Helvetica', 10)
    page.drawString(130,
                    560,
                    'Total Species collection: {0}'.format(species_total))
    page.drawImage(biodiversity_logo, 90, 500, width = 30, height = 30,
                   preserveAspectRatio = True, mask = 'auto')

    page.setFont('Times-Roman', 10)
    page.drawString(130,
                    510,
                    'Total Biological records: {0}'.format(biological_total))

    page.setFont('Helvetica-Bold', 12)
    page.drawString(90,
                    450,
                    'Environmental impact management role')
    page.showPage()
    page.save()


def view_pdf(request):

    current_site = request.META['HTTP_HOST']
    pdf_name = 'ledet_report_' + strftime("%Y-%m-%d %H:%M:%S", gmtime())

    filename = '{}.{}'.format(pdf_name, 'pdf')
    storage_folder = 'reports'
    pathname = \
        os.path.join(
            '/home/web/media', '{}/{}'.format(storage_folder, filename))
    found = os.path.exists(pathname)
    if found:
        with open(pathname, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = \
                'filename={}.pdf'.format(pdf_name)
            return response
    else:
        makepath = '/home/web/media/{}/'.format(storage_folder)
        if not os.path.exists(makepath):
            os.makedirs(makepath)

        create_pdf(pathname, current_site)
        with open(pathname, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = \
                'filename={}.pdf'.format(pdf_name)
            return response
