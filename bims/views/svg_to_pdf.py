import os
import re
import hashlib
from datetime import datetime
from tempfile import NamedTemporaryFile
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound


def _hex_to_rgb(hex_color):
    """Convert a hex color string to rgb() format for svglib compatibility."""
    # Remove # prefix if present
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        # Expand shorthand #RGB to #RRGGBB
        hex_color = ''.join([c*2 for c in hex_color])
    if len(hex_color) != 6:
        return None  # Invalid, skip conversion
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgb({r},{g},{b})'
    except (ValueError, IndexError):
        return None


def _preprocess_svg_colors(svg_content):
    """
    Convert hex colors in SVG to rgb() format for svglib compatibility.
    svglib has issues parsing hex colors like #18A090.
    """
    # Find all hex color patterns and replace them
    # This handles: #RGB, #RRGGBB in any context
    def replace_hex(match):
        rgb = _hex_to_rgb(match.group(0))
        return rgb if rgb else match.group(0)

    # Match # followed by exactly 3 or 6 hex digits
    # Use word boundary or lookahead to avoid matching too much
    hex_pattern = r'#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])'
    return re.sub(hex_pattern, replace_hex, svg_content)


def _ensure_hex_color(color_value, default='#18A090'):
    """Ensure color value is a valid hex color string for ReportLab."""
    if not color_value:
        return default
    color_str = str(color_value).strip()
    # Ensure it starts with #
    if not color_str.startswith('#'):
        color_str = f'#{color_str}'
    # Validate it looks like a hex color
    if len(color_str) not in (4, 7, 9):  # #RGB, #RRGGBB, #RRGGBBAA
        return default
    try:
        # Verify all characters after # are hex digits
        int(color_str[1:], 16)
    except ValueError:
        return default
    return color_str


def get_theme_colors():
    """Get theme colors from CustomTheme or return defaults."""
    try:
        from bims_theme.models.theme import CustomTheme
        theme = CustomTheme.objects.filter(is_enabled=True).first()
        if theme:
            return {
                'primary': _ensure_hex_color(theme.main_accent_color, '#18A090'),
                'secondary': _ensure_hex_color(theme.secondary_accent_color, '#DBAF00'),
                'text': _ensure_hex_color(theme.main_button_text_color, '#FFFFFF'),
                'site_name': theme.site_name or 'BIMS',
                'logo_path': theme.logo.path if theme.logo else None,
                'navbar_logo_path': theme.navbar_logo.path if theme.navbar_logo else None,
            }
    except Exception:
        pass
    return {
        'primary': '#18A090',
        'secondary': '#DBAF00',
        'text': '#FFFFFF',
        'site_name': 'BIMS',
        'logo_path': None,
        'navbar_logo_path': None,
    }


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
    """Convert SVG string to a professionally branded PDF with title and theming."""

    if request.method != 'POST':
        return HttpResponseNotFound('Request not found')
    svg = request.POST.get('svg', None)
    title = request.POST.get('title', '')
    if not svg:
        return HttpResponseNotFound('SVG string not found')

    # Get theme colors
    theme = get_theme_colors()
    primary_color = colors.HexColor(theme['primary'])

    folder = 'charts'
    path_folder = os.path.join(settings.MEDIA_ROOT, folder)
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)
    path_folder = os.path.join(path_folder,
                               '{}'.format(
                                   hashlib.sha256(
                                       svg.encode('utf-8')).hexdigest()))
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)

    path_file = os.path.join(path_folder, '{}.pdf'.format(title))

    # Preprocess SVG to convert hex colors to rgb() for svglib compatibility
    svg = _preprocess_svg_colors(svg)

    svg_file = NamedTemporaryFile(delete=False, mode='w', suffix='.svg')
    with open(svg_file.name, 'w') as f_svg:
        f_svg.write(svg)

    max_width, max_height = A4
    svg_canvas = canvas.Canvas(path_file, pagesize=A4)

    # Draw header bar with primary color
    svg_canvas.setFillColor(primary_color)
    svg_canvas.rect(0, max_height - 50, max_width, 50, fill=1, stroke=0)

    # Draw header text
    svg_canvas.setFillColor(colors.white)
    svg_canvas.setFont('Helvetica-Bold', 14)
    svg_canvas.drawString(20, max_height - 32, theme['site_name'])

    # Draw title below header
    svg_canvas.setFillColor(colors.HexColor('#333333'))
    svg_canvas.setFont('Helvetica-Bold', 18)
    svg_canvas.drawString(20, max_height - 80, title)

    # Draw the SVG chart
    try:
        drawing = svg2rlg(svg_file.name)
    except AttributeError as e:
        # svglib may fail to parse hex colors - clean up and re-raise with context
        svg_file.close()
        os.unlink(svg_file.name)
        error_msg = str(e)
        if "has no attribute '#" in error_msg:
            raise ValueError(
                f"SVG contains a color that svglib cannot parse: {error_msg}. "
                "Try using named colors (e.g., 'blue') instead of hex codes."
            ) from e
        raise
    svg_width = request.POST.get('svgWidth', None)
    if svg_width:
        svg_width = float(svg_width)
    else:
        svg_width = drawing.width

    # Calculate scale to fit within page (leaving margins for header/footer)
    available_width = max_width - 40  # 20px margins on each side
    available_height = max_height - 160  # Space for header and footer
    drawing_scale = min(available_width / svg_width, 1.0)

    scaled_drawing = scale(drawing, scaling_factor=drawing_scale)
    renderPDF.draw(scaled_drawing, svg_canvas, 20,
                   max_height - scaled_drawing.height - 100)

    # Draw footer bar
    svg_canvas.setFillColor(colors.Color(0.95, 0.95, 0.95))
    svg_canvas.rect(0, 0, max_width, 40, fill=1, stroke=0)

    # Footer line
    svg_canvas.setStrokeColor(primary_color)
    svg_canvas.setLineWidth(2)
    svg_canvas.line(0, 40, max_width, 40)

    # Footer text
    svg_canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
    svg_canvas.setFont('Helvetica', 8)
    generated_text = f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}"
    svg_canvas.drawString(20, 15, generated_text)

    # Try to use theme logo, fall back to stamp if not available
    logo_path = theme.get('navbar_logo_path') or theme.get('logo_path')
    if logo_path and os.path.exists(logo_path):
        try:
            svg_canvas.drawImage(
                logo_path,
                max_width - 80,
                8,
                width=50,
                height=24,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            # Fall back to default stamp
            stamp = os.path.join(settings.STATIC_ROOT, 'img/bims-stamp.png')
            if os.path.exists(stamp):
                svg_canvas.drawImage(stamp, max_width - 80, 8, mask='auto')
    else:
        # Use default stamp
        stamp = os.path.join(settings.STATIC_ROOT, 'img/bims-stamp.png')
        if os.path.exists(stamp):
            svg_canvas.drawImage(stamp, max_width - 80, 8, mask='auto')

    svg_canvas.save()
    svg_file.close()
    os.unlink(svg_file.name)
    return HttpResponse(
        path_file.replace(settings.MEDIA_ROOT, settings.MEDIA_URL))
