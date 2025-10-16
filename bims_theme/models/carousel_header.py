# coding=utf-8
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from ordered_model.models import OrderedModel
from colorfield.fields import ColorField


class CarouselHeader(OrderedModel):
    ALIGNMENT_OPTIONS = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justify'),
    ]

    STYLE_OPTIONS = [
        ('normal', 'Normal'),
        ('bold', 'Bold'),
        ('italic', 'Italic'),
    ]

    BANNER_FIT_CHOICES = [
        ('cover', 'Cover (fill area, crop if needed)'),
        ('contain', 'Contain (no crop)'),
        ('natural', 'Natural size'),
        ('stretch', 'Stretch to fill'),
    ]
    BANNER_HEIGHT_MODE_CHOICES = [
        ('auto', 'Auto (image height)'),
        ('fixed_px', 'Fixed (px)'),
        ('viewport_vh', 'Viewport (vh)'),
    ]
    POS_CHOICES = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('top', 'Top'),
        ('bottom', 'Bottom'),
    ]

    banner = models.ImageField(upload_to='banner')

    title = models.TextField(blank=True, default='', help_text='Title of the carousel')
    description = models.TextField(blank=True, default='', verbose_name='Paragraph', help_text='Paragraph inside carousel')

    text_color = ColorField(default='#FFFFFF', help_text='Color of the text inside carousel')

    background_color_overlay = ColorField(default='#FFFFFF', help_text='Background color overlay behind the text')

    background_overlay_opacity = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Opacity of the background overlay, in percentage'
    )

    text_alignment = models.CharField(
        max_length=7, choices=ALIGNMENT_OPTIONS, default='left',
        help_text='Default alignment for both title and description.'
    )
    text_style = models.CharField(
        max_length=6, choices=STYLE_OPTIONS, default='normal',
        help_text='Default text style for title/description (fallback).'
    )
    title_font_size = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(80)],
        default=45, help_text='Default title size (10–80).'
    )
    description_font_size = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        default=30, help_text='Default description size (10–50).'
    )

    banner_fit = models.CharField(
        max_length=10, choices=BANNER_FIT_CHOICES, default='cover',
        help_text='How the image scales in the banner.'
    )
    banner_height_mode = models.CharField(
        max_length=12, choices=BANNER_HEIGHT_MODE_CHOICES, default='viewport_vh',
        help_text='How the banner height is determined.'
    )
    banner_height_value = models.PositiveIntegerField(
        default=60,
        help_text='Height value in px (when fixed_px) or vh (when viewport_vh). Ignored for auto.'
    )
    banner_position_x = models.CharField(
        max_length=6, choices=[('left','Left'), ('center','Center'), ('right','Right')],
        default='center', help_text='Horizontal focal point.'
    )
    banner_position_y = models.CharField(
        max_length=6, choices=[('top','Top'), ('center','Center'), ('bottom','Bottom')],
        default='center', help_text='Vertical focal point.'
    )
    title_font = models.ForeignKey(
        'bims_theme.CustomFont',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='carousel_title_font',
    )
    title_font_weight = models.CharField(
        max_length=3,
        choices=[('300','Light 300'), ('400','Regular 400'), ('500','Medium 500'), ('600','Semibold 600'), ('700','Bold 700')],
        default='700',
        help_text='Title font weight.',
    )
    title_letter_spacing_em = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.00,
        help_text='Title letter spacing in em (e.g., 0.00, 0.05).'
    )
    title_alignment = models.CharField(
        max_length=7, choices=ALIGNMENT_OPTIONS, blank=True, default='',
        help_text='Override alignment for title only (empty = use default).'
    )
    title_offset_y_percent = models.PositiveIntegerField(
        default=30, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Vertical position of title (0–100%, from top).'
    )
    title_line_height_pct = models.PositiveIntegerField(
        default=110, validators=[MinValueValidator(80), MaxValueValidator(200)],
        help_text='Title line-height as percent.'
    )

    description_font = models.ForeignKey(
        'bims_theme.CustomFont',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='carousel_description_font',
    )

    description_font_weight = models.CharField(
        max_length=3,
        choices=[('300','Light 300'), ('400','Regular 400'), ('500','Medium 500'), ('600','Semibold 600'), ('700','Bold 700')],
        default='400', help_text='Description font weight.'
    )
    description_letter_spacing_em = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.00,
        help_text='Description letter spacing in em.'
    )
    description_alignment = models.CharField(
        max_length=7, choices=ALIGNMENT_OPTIONS, blank=True, default='',
        help_text='Override alignment for description only (empty = use default).'
    )
    description_offset_y_percent = models.PositiveIntegerField(
        default=12, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Offset below the title in percent of slide height.'
    )
    description_line_height_pct = models.PositiveIntegerField(
        default=130, validators=[MinValueValidator(80), MaxValueValidator(200)],
        help_text='Description line-height as percent.'
    )

    full_screen_background = models.BooleanField(
        default=False, help_text='Legacy. Prefer banner_fit.')

    class Meta:
        verbose_name_plural = 'Carousel Headers'
        ordering = ['order']

    def __str__(self):
        if self.title:
            return self.title
        if self.banner:
            return self.banner.name
        return f'Carousel Header - {self.id}'
