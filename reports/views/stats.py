__author__ = 'Alison Mukoma <alison@kartoza.com'
__copywrite__ = 'kartoza.com'

import os

from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape


def create_pdf(pathname, current_site):

    # initialising the PDF for drawing content on it
    page = canvas.Canvas(pathname, pagesize=landscape(A4))
    width, height = A4
    center = height * 0.5

    margin_right = height - 50
    margin_left = 50
    margin_bottom = 50

    # we start to draw staff on the PDF
    page.setFillColorRGB(0.1, 0.1, 0.1)
    page.setFont('Times-Roman', 18)

    page.setFont('Times-Bold', 26)
    page.drawCentredString(center, 480, 'Ledet Report')

    page.setFont('Times-Roman', 16)
    page.drawCentredString(
        center, 370, 'Here we shall count some things like fish.. maybe more')

    # footer information.
    page.setFont('Times-Roman', 14)
    page.drawString(
        margin_left,
        margin_bottom - 10,
        'We are still adding staff to this report.')
    page.setFont('Times-Roman', 8)

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
