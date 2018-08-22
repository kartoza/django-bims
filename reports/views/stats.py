__author__ = 'Alison Mukoma <alison@kartoza.com'
__copywrite__ = 'kartoza.com'


import os
import datetime
from time import gmtime, strftime

from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import ELEVENSEVENTEEN
from reportlab.graphics.charts.barcharts import VerticalBarChart

from bims.models.taxon import Taxon
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord


def create_pdf(pathname, current_site):

    # initialising the PDF for drawing content on it
    page = canvas.Canvas(pathname, pagesize=ELEVENSEVENTEEN)


    margin_left = 50
    margin_bottom = 1150
    page.setFont('Helvetica-Bold', 20)
    page.drawString(margin_left + 200, margin_bottom + 10,
                    'KBIMS species - Focused Report')
    now = datetime.date.today()
    time = now.strftime('%d, %b %Y')
    page.setFont('Helvetica', 10)
    page.drawString(
            margin_left + 300,
            margin_bottom - 10,
            'Date: {}'.format(time))

    # SECTION: OVERVIEW

    present_records = BiologicalCollectionRecord.objects.filter(
            present=True).count()

    absent_records = BiologicalCollectionRecord.objects.filter(
            absent   =True).count()

    validation_ready = BiologicalCollectionRecord.objects.filter(
            ready_for_validation=True).count()

    validation_not_ready = BiologicalCollectionRecord.objects.filter(
            ready_for_validation=False).count()

    validated = BiologicalCollectionRecord.objects.filter(
            validated=True).count()


    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left, margin_bottom - 30,
                    'Overview')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 5, margin_bottom - 90,
                    'Rank')


    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 300, margin_bottom - 90,
                    'Species')

    page.line(
            (margin_left + 5), (margin_bottom - 105),
            (margin_left + 360), (margin_bottom - 105))

    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 5, margin_bottom - 100,
    #                 'Present Records')
    #
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 200, margin_bottom - 100,
    #                 '636268')
    #
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 300, margin_bottom - 100,
    #                 '636268')

    page.line(
            (margin_left + 5), (margin_bottom - 125),
            (margin_left + 360), (margin_bottom - 125))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 120,
                    'Present records')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 120,
                    str(present_records))

    page.line(
            (margin_left + 5), (margin_bottom - 145),
            (margin_left + 360), (margin_bottom - 145))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 140,
                    'Absent records')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 140,
                    str(absent_records))

    page.line(
            (margin_left + 5), (margin_bottom - 165),
            (margin_left + 360), (margin_bottom - 165))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 160,
                    'Ready for validtation')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 160,
                    str(validation_ready))

    page.line(
            (margin_left + 5), (margin_bottom - 185),
            (margin_left + 360), (margin_bottom - 185))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 180,
                    'Not ready for Validation')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 180,
                    str(validation_not_ready))

    page.line(
            (margin_left + 5), (margin_bottom - 205),
            (margin_left + 360), (margin_bottom - 205))
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 200,
                    'Validated')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 200,
                    str(validated))


    # Taxonomy from (from specified source)

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left, margin_bottom - 280,
                    'Taxonomy (from: Tinca tinca)')

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
            (margin_left + 360), (margin_bottom - 305))

    # insert a 30 value difference on height
    # TODO: implement a user defined query for which Taxon they
    # want to see details for.

    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 5, margin_bottom - 330,
    #                 'Kingdom')
    # # query to fetch specie family details.
    # # anguillidae = Taxon.objects.get(family='Anguillidae')
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 105, margin_bottom - 330,
    #                 'Anguillidae')
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 205, margin_bottom - 330,
    #                 'anguillidae.author')
    # page.setFont('Helvetica', 12)
    # page.drawString(margin_left + 305, margin_bottom - 330,
    #                 'record')
    # tinca_tinca_record = Taxon.objects.get(common_name='Tinca tinca')
    tinca_record = Taxon.objects.get(genus='Tinca')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 330,
                    'Kingdom')
    # query to fetch specie family details.
    # anguillidae = Taxon.objects.get(family='Anguillidae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 330,
                    'taxon_record.kingdom')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 330,
                    'tinca_record.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 330,
                    'tinca_record.gbif_id')

    # ------------------------------------------
    page.line(
            (margin_left + 5), (margin_bottom - 335),
            (margin_left + 380), (margin_bottom - 335))


    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 350,
                    'Phylum')
    # atherinidae = Taxon.objects.get(family='Atherinidae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 350,
                    'Atherinidae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 350,
                    'atherinidae.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 350,
                    'records')

    page.line(
            (margin_left + 5), (margin_bottom - 355),
            (margin_left + 380), (margin_bottom - 355))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 370,
                    'Class')
    # austroglanididae = Taxon.objects.get(family='Austroglanididae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 370,
                    'Austroglanididae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 370,
                    'austroglanididae.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 370,
                    'records')

    page.line(
            (margin_left + 5), (margin_bottom - 375),
            (margin_left + 380), (margin_bottom - 375))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 390,
                    'Order')
    # emberizidae = Taxon.objects.get(family='Emberizidae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 390,
                    'Emberizidae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 390,
                    'emberizidae.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 390,
                    'records')

    page.line(
            (margin_left + 5), (margin_bottom - 395),
            (margin_left + 380), (margin_bottom - 395))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 410,
                    'Family')
    # cyprinidae = Taxon.objects.get(family='Cyprinidae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 410,
                    'Cyprinidae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 410,
                    'cyprinidae.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 410,
                    'records')

    page.line(
            (margin_left + 5), (margin_bottom - 415),
            (margin_left + 380), (margin_bottom - 415))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 430,
                    'Genus')
    # mugilidae = Taxon.objects.get(family='Mugilidae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 430,
                    'Mugilidae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 430,
                    'mugilidae.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 430,
                    'records')
    page.line(
            (margin_left + 5), (margin_bottom - 435),
            (margin_left + 380), (margin_bottom - 435))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 450,
                    'Species')
    # Cyprinidae = Taxon.objects.get(family='Cyprinidae')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 105, margin_bottom - 450,
                    'Cyprinidae')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 205, margin_bottom - 450,
                    'Cyprinidae.author')
    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 305, margin_bottom - 450,
                    'records')
    page.line(
            (margin_left + 5), (margin_bottom - 455),
            (margin_left + 380), (margin_bottom - 455))


    # SPECIES DATABASE BREAKDOWN

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left, margin_bottom - 550,
                    'SPECIES DATABASE BREAKDOWN')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 5, margin_bottom - 580,
                    'Rank')

    page.setFont('Helvetica-Bold', 14)
    page.drawString(margin_left + 300, margin_bottom - 580,
                    'Species')

    page.line(
            (margin_left + 5), (margin_bottom - 605),
            (margin_left + 360), (margin_bottom - 605))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 630,
                    'Native')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 630,
                    'native record count')
    page.line(
            (margin_left + 5), (margin_bottom - 635),
            (margin_left + 360), (margin_bottom - 635))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 660,
                    'Non Native')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 660,
                    'none-native record count')
    page.line(
            (margin_left + 5), (margin_bottom - 665),
            (margin_left + 360), (margin_bottom - 665))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 690,
                    'Translocated')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 690,
                    'translocated count')
    page.line(
            (margin_left + 5), (margin_bottom - 695),
            (margin_left + 360), (margin_bottom - 695))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 720,
                    'Species Richness')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 720,
                    'species richness count')
    page.line(
            (margin_left + 5), (margin_bottom - 725),
            (margin_left + 360), (margin_bottom - 725))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 750,
                    'Shannon Diversity')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 750,
                    'Shannon Diversity count')
    page.line(
            (margin_left + 5), (margin_bottom - 755),
            (margin_left + 360), (margin_bottom - 755))

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 5, margin_bottom - 780,
                    'Simpson Diversity')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 300, margin_bottom - 780,
                    'Simpson Diversity count')
    page.line(
            (margin_left + 5), (margin_bottom - 785),
            (margin_left + 360), (margin_bottom - 785))

    # SECTION: ENVIRONMENTAL CONDITIONS

    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left + 410, margin_bottom - 70,
                    'Biological collection records: {}'.format(
                            BiologicalCollectionRecord.objects.count()))
    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left + 410, margin_bottom - 90,
                    'Environmental conditions')

    page.setFont('Helvetica', 12)
    page.drawString(margin_left + 410, margin_bottom - 110,
                    'Temperature')

    drawing = Drawing(margin_left + 410, margin_bottom - 100)

    data = [
        (32, 15, 20, 22, 37, 98, 21, 9),
    ]

    max_x = list(range(-5, 30, 5))
    names = ["%s" % i for i in max_x]

    bar_chart = VerticalBarChart()
    bar_chart.x = 20
    bar_chart.y = 50
    bar_chart.height = 100
    bar_chart.width = 250
    bar_chart.data = data
    bar_chart.strokeColor = colors.white
    bar_chart.valueAxis.valueMin = 0
    bar_chart.valueAxis.valueMax = 1527
    bar_chart.valueAxis.valueStep = 500
    bar_chart.categoryAxis.labels.boxAnchor = 'ne'
    bar_chart.categoryAxis.labels.dx = -10
    bar_chart.categoryAxis.labels.fontName = 'Helvetica'
    bar_chart.categoryAxis.categoryNames = names

    drawing.add(bar_chart)
    drawing.drawOn(page, margin_left + 410, margin_bottom - 300)

    page.showPage()
    # --------------------------------------
    species = Taxon.objects.all()
    species_list = list(species)
    species_total = Taxon.objects.all().count()
    page.setFont('Helvetica-Bold', 16)
    page.drawString(margin_left + 5, margin_bottom - 10,
                    'PLACE FOCUSED DETAILS(Showing the first 50 '
                    'results of %s)' % (species_total))

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 5, margin_bottom - 40,
                    'Common name')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 120, margin_bottom - 40,
                    'Species Name')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 340, margin_bottom - 40,
                    'Family')

    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 420, margin_bottom - 40,
                    'Genus')
    page.setFont('Helvetica-Bold', 12)
    page.drawString(margin_left + 520, margin_bottom - 40,
                    'IUCN Status')

    page.line(
            (margin_left + 5), (margin_bottom - 45),
            (margin_left + 590), (margin_bottom - 45))

    specie_left_margin = margin_left + 5
    specie_bottom_margin = margin_bottom - 60

    for taxa in species_list[:50]:
        page.setFont('Helvetica', 8)
        page.drawString(specie_left_margin, specie_bottom_margin,
                        taxa.common_name)

        page.setFont('Helvetica', 8)
        page.drawString(
                specie_left_margin + 115,
                specie_bottom_margin, taxa.scientific_name)

        page.setFont('Helvetica', 8)
        page.drawString(
                specie_left_margin + 340,
                specie_bottom_margin, taxa.family)

        page.setFont('Helvetica', 8)
        page.drawString(
                specie_left_margin + 420,
                specie_bottom_margin, taxa.genus)

        page.setFont('Helvetica', 8)
        page.drawString(
                specie_left_margin + 520,
                specie_bottom_margin, str(taxa.iucn_status))

        specie_bottom_margin = (specie_bottom_margin - 20)

    # second page
    page.showPage()
    page.save()


def view_pdf(request):

    current_site = request.META['HTTP_HOST']
    pdf_name = 'kbims_report_{}'.format(strftime("%Y-%m-%d"+'_'+
                                                  "%H:%M:%S",
                                         gmtime()))

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
