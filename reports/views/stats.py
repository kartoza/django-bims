__author__ = 'Alison Mukoma <alison@kartoza.com'
__copywrite__ = 'kartoza.com'

import os
from time import gmtime, strftime
import datetime

from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import ELEVENSEVENTEEN
from reportlab.graphics.charts.barcharts import VerticalBarChart

from bims.models.taxon import Taxon
from bims.models.biological_collection_record import BiologicalCollectionRecord

def create_pdf(pathname, current_site):

    # initialising the PDF for drawing content on it
    # page = canvas.Canvas(pathname, pagesize=landscape(A4))
    page = canvas.Canvas(pathname, pagesize=ELEVENSEVENTEEN)

    # page.radialGradient(105 * mm, 240 * mm, 60 * mm, (darkred, yellow,
    #                                             yellowgreen), (0, 0.8, 1))

    # wildlife_logo = 'reports/static/img/collection/wildlife.png'
    # biodiversity_logo = 'reports/static/img/collection/biodiversity.png'
    # page.setFont('Helvetica-Bold', 16)
    #
    # page.drawImage(
    #         logo, 250, 650, width = 100, height = 100,
    #         preserveAspectRatio = True, mask = 'auto')
    # page.drawString(255, 500, 'Ledet Report')

    # page.setFont('Helvetica-Bold', 12)
    # page.drawString(220,
    #                 600,
    #                 'Protected area management role')
    # now = datetime.date.today()
    # time = now.strftime('%d, %b %Y')
    #
    # page.setFont('Helvetica', 10)
    # page.drawString(260,
    #                 580,
    #                 'Date: {}'.format(time))
    margin_left = 50
    margin_bottom = 1150
    page.setFont('Helvetica-Bold', 20)
    page.drawString(margin_left + 200, margin_bottom + 10,
                    'LBIMS species - Focused report')

    # SECTION: OVERVIEW

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left, margin_bottom - 30,
                    'Overview')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 5,  margin_bottom - 70,
                    'Rank')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 300, margin_bottom - 70,
                    'Species')

    page.line(
            (margin_left + 5), (margin_bottom - 105),
            (margin_left + 380), (margin_bottom - 105))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 100,
                    'OBIS ID')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 100,
                    '636268')

    page.line(
            (margin_left + 5), (margin_bottom - 125),
            (margin_left + 380), (margin_bottom - 125))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 120,
                    'Valid OBIS ID')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 120,
                    '636268')

    page.line(
            (margin_left + 5), (margin_bottom - 145),
            (margin_left + 380), (margin_bottom - 145))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 140,
                    'Aphia ID')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 140,
                    '127081')

    page.line(
            (margin_left + 5), (margin_bottom - 165),
            (margin_left + 380), (margin_bottom - 165))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 160,
                    'Records')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 160,
                    '100, 768')

    page.line(
            (margin_left + 5), (margin_bottom - 185),
            (margin_left + 380), (margin_bottom - 185))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 180,
                    'Datasets')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 180,
                    '60')

    page.line(
            (margin_left + 5), (margin_bottom - 205),
            (margin_left + 380), (margin_bottom - 205))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 200,
                    'Red List status')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 200,
                    'LC')

    page.line(
            (margin_left + 5), (margin_bottom - 225),
            (margin_left + 380), (margin_bottom - 225))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 220,
                    'Global Invasive Species Database')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 220,
                    '-')

    page.line(
            (margin_left + 5), (margin_bottom - 245),
            (margin_left + 380), (margin_bottom - 245))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5,  margin_bottom - 240,
                    'Hamful Micro Algae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300,  margin_bottom - 240,
                    '-')


    # Taxonomy from (from specified source)

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left, margin_bottom - 280,
                    'Taxonomy (from WORMS)')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 5, margin_bottom - 300,
                    'Rank')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 105, margin_bottom - 300,
                    'Taxon')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 205, margin_bottom - 300,
                    'Author')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 305, margin_bottom - 300,
                    'Records')

    # set an additional 5 to bottom differenct on the line so as we
    #  have a little margin-botton on the text
    page.line(
            (margin_left + 5), (margin_bottom - 305),
            (margin_left + 380), (margin_bottom - 305))

    # insert a 30 value difference on height

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 330,
                    'Kingdom')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 330,
                    'Animalia')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 330,
                    'Haekel, 1874')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 330,
                    '25,732,563')

    # ------------------------------------------
    page.line(
            (margin_left + 5), (margin_bottom - 335),
            (margin_left + 380), (margin_bottom - 335))

    # insert a 30 value difference on height

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 360,
                    'Kingdom')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 360,
                    'Animalia')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 360,
                    'Haekel, 1874')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 360,
                    '25,732,563')

    # SECTION: RECORDS PER AREA

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left, margin_bottom - 400,
                    'Records per area')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 5, margin_bottom - 420,
                    'Area')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 105, margin_bottom - 420,
                    'Records')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 205, margin_bottom - 420,
                    '%')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 305, margin_bottom - 420,
                    'Since')

    # set an additional 5 to bottom differenct on the line so as we
    #  have a little margin-botton on the text
    page.line(
            (margin_left + 5), (margin_bottom - 425),
            (margin_left + 380), (margin_bottom - 425))

    # insert a 30 value difference on height

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 440,
                    'North Atlantic')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 440,
                    '17, 433')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 440,
                    '17')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 440,
                    '1957')

    # ------------------------------------------
    page.line(
            (margin_left + 5), (margin_bottom - 445),
            (margin_left + 380), (margin_bottom - 445))

    # insert a 30 value difference on height

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 460,
                    'Kingdom')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 460,
                    'Animalia')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 460,
                    'Haekel, 1874')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 460,
                    '25,732,563')

    # SECTION: SPECIES DISTRIBUTION

    from bims.models import Taxon


    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left + 5, margin_bottom - 550,
                    'SPECIES FOCUSED DETAILS')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 5,  margin_bottom - 600,
                    'Common name')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 210, margin_bottom - 600,
                    'Species Name')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 510, margin_bottom - 600,
                    'Origin')


    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 610, margin_bottom - 600,
                    '# Records')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 710, margin_bottom - 600,
                    '# Sites')

    page.line(
            (margin_left + 5), (margin_bottom - 605),
            (margin_left + 700), (margin_bottom - 605))


    # specie_left_margin = margin_left + 5
    # specie_bottom_margin = margin_bottom + 620


    specie_left_margin = margin_left + 5
    specie_bottom_margin = margin_bottom - 620

    from bims.models import BiologicalCollectionRecord


    species = Taxon.objects.all()

    for taxa in species:

        record_site = BiologicalCollectionRecord.objects.filter(
                taxon_gbif_id=taxa.gbif_id)

        page.setFont('Helvetica-Bold', 12)
        page.drawString(specie_left_margin, specie_bottom_margin,
                        taxa.common_name)
        # page.setFont('Helvetica-Bold', 12)
        # page.drawString(specie_left_margin, specie_bottom_margin,
        #                 'English Name')

        page.setFont('Helvetica-Bold', 12)
        page.drawString(specie_left_margin + 210, \
                                               specie_bottom_margin,
                        taxa.scientific_name)

        page.setFont('Helvetica-Bold', 12)
        page.drawString(specie_left_margin + 510,
                        specie_bottom_margin,
                        taxa.family)

        page.setFont('Helvetica-Bold', 12)
        page.drawString(specie_left_margin + 610,
                        specie_bottom_margin,
                        '# Records')

        page.setFont('Helvetica-Bold', 12)
        page.drawString(specie_left_margin + 710,
                        specie_bottom_margin,
                        record_site.count())


        # specie_left_margin = specie_left_margin
        specie_bottom_margin = (specie_bottom_margin - 20)


    # SECTION: IMAGES - right section

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left + 410, margin_bottom - 70,
                    'Images')

    page.line(
            (margin_left + 410), (margin_bottom - 80),
            (margin_left + 800), (margin_bottom - 80))

    # insert a 30 value difference on height


    fish_image = 'reports/static/img/fishes.png'

    page.drawImage(
            fish_image, margin_left + 410, margin_bottom - 290,
            width = 300,
            height = 200,
            preserveAspectRatio = True, mask = 'auto')
            # page.drawString(255, 500, 'fish images')

    # SECTION: ENVIRONMENTAL CONDITIONS

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left + 410, margin_bottom - 350,
                    'Environmental conditions')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 410,  margin_bottom - 400,
                    'Temperature')


    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 500, margin_bottom - 400,
    #                 'Salinity')
    #
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 600, margin_bottom - 400,
    #                 'Depth')


    drawing = Drawing(margin_left + 410,  margin_bottom - 600)


    data = [
        (13, 5, 20, 22, 37, 98, 19, 4),
    ]

    max_x = list(range(-5, 30, 5))
    names = ["%s" % i for i in max_x]

    bc = VerticalBarChart   ()
    bc.x = 20
    bc.y = 50
    bc.height = 100
    bc.width = 250
    bc.data = data
    bc.strokeColor = colors.white
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 1527
    bc.valueAxis.valueStep = 500
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = -10
    bc.categoryAxis.labels.fontName = 'Helvetica'
    bc.categoryAxis.categoryNames = names

    drawing.add(bc)
    drawing.drawOn(page, margin_left + 410, margin_bottom - 600)

    # SECTION: COMMON NAMES
    #
    # page.setFont('Helvetica-Bold', 16)
    # page.drawString(margin_left + 5, margin_bottom - 900,
    #                 'Common names')
    #
    # page.setFont('Helvetica-Bold', 14)
    # page.drawString(margin_left + 5,  margin_bottom - 1000,
    #                 'Name')
    #
    # page.setFont('Helvetica-Bold', 14)
    # page.drawString(margin_left + 205, margin_bottom - 1000,
    #                 'Language')
    #
    # page.line(
    #         (margin_left + 5), (margin_bottom - 1005),
    #         (margin_left + 380), (margin_bottom - 1005))
    #
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 5,  margin_bottom - 2000,
    #                 'Bonito')
    #
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 205,  margin_bottom - 2000,
    #                 'English')

    # page.setFillColorRGB(0.1, 0.1, 0.1)
    # page.setFont('Helvetica-Bold', 14)
    # page.drawString(
    #         380, 500, 'Common names')
    #
    #
    # name_height = 480
    # status_height = 420
    #
    # for specie in species_records:
    #
    #     page.setFillColorRGB(0.1, 0.1, 0.1)
    #     page.setFont('Helvetica', 12)
    #     page.drawString(
    #             380, 420, 'Species Name')
    #
    #     page.setFont('Helvetica', 10)
    #     page.drawString(
    #             380, name_height, specie.scientific_name)
    #
    #     page.setFillColorRGB(0.1, 0.1, 0.1)
    #     page.setFont('Helvetica', 12)
    #     page.drawString(
    #             520, 420, 'IUCN Status')
    #
    #     page.setFont('Helvetica', 10)
    #     page.drawString(
    #             400, status_height, 'Available')
    #
    #     name_height -= 20
    #     status_height -= 20



    # page.drawImage(biodiversity_logo, 90, 500, width = 30, height = 30,
    #                preserveAspectRatio = True, mask = 'auto')

    # page.setFont('Times-Roman', 10)
    # page.drawString(130,
    #                 510,
    #                 'Total Biological records: {0}'.format(biological_total))
    #
    # page.setFont('Helvetica-Bold', 12)
    # page.drawString(90,
    #                 450,
    #                 'Environmental impact management role')
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
