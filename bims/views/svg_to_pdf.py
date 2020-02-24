import os
import hashlib
from tempfile import NamedTemporaryFile
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound


def scale(drawing, scaling_factor):
    """
    Scale a reportlab.graphics.shapes.Drawing()
    object while maintaining the aspect ratio
    """
    scaling_x = scaling_factor
    scaling_y = scaling_factor

    drawing.width = drawing.minWidth() * scaling_x
    drawing.height = drawing.height * scaling_y
    drawing.scale(scaling_x, scaling_y)
    return drawing


def svg_to_pdf(request):
    # Convert svg string to pdf with title and stamp

    if request.method != 'POST':
        return HttpResponseNotFound('Request not found')
    svg = request.POST.get('svg', None)
    title = request.POST.get('title', '')
    if not svg:
        return HttpResponseNotFound('SVG string not found')

    folder = 'charts'
    path_folder = os.path.join(settings.MEDIA_ROOT, folder)
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)
    path_folder = os.path.join(path_folder,
                               '{}'.format(hashlib.md5(svg).hexdigest()))
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)

    path_file = os.path.join(path_folder, '{}.pdf'.format(title))
    svg_file = NamedTemporaryFile(delete=False)
    with open(svg_file.name, svg_file.mode) as f_svg:
        f_svg.write(svg)
    max_width, max_height = A4
    svg_canvas = canvas.Canvas(path_file, pagesize=A4)
    drawing = svg2rlg(svg_file.name)
    drawing_scale = max_width / drawing.width
    if drawing_scale > 1:
        drawing_scale = 1
    scaled_drawing = scale(drawing, scaling_factor=drawing_scale)
    renderPDF.draw(scaled_drawing, svg_canvas, 0,
                   max_height - scaled_drawing.height - 80)
    svg_canvas.setFont('Helvetica-Bold', 20)
    svg_canvas.drawString(40, max_height - 50, title)

    # Stamp logo
    stamp = os.path.join(settings.STATIC_ROOT, 'img/bims-stamp.png')
    svg_canvas.drawImage(
        stamp,
        max_width - 100,
        30,
        mask='auto'
    )

    svg_canvas.save()
    svg_file.close()
    os.unlink(svg_file.name)
    return HttpResponse('OK')
