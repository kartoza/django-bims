# coding=utf-8
"""Landing page section model definition.

"""
from colorfield.fields import ColorField
from django.db import models
from ordered_model.models import OrderedModel


BACKGROUND_FIT_CHOICES = [
    ('cover', 'Cover (fill area, crop if needed)'),
    ('contain', 'Contain (no crop)'),
    ('natural', 'Natural size'),
    ('stretch', 'Stretch to fill'),
]

HEIGHT_MODE_CHOICES = [
    ('auto', 'Auto (image height)'),
    ('fixed_px', 'Fixed (px)'),
    ('viewport_vh', 'Viewport (vh)'),
]


class LandingPageSection(OrderedModel):
    """Landing page section model."""
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text=(
            'Name of the section, for identifier only, '
            'will not appear in landing page'
        )
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Title of the section, may be left blank'
    )

    contents = models.ManyToManyField(
        'bims_theme.LandingPageSectionContent',
        blank=True
    )

    background_color = ColorField(
        default='#FFFFFF',
        help_text='Background color for the section'
    )

    background = models.ImageField(
        blank=True,
        null=True,
        upload_to='landing_page_section_background',
        help_text=(
            "Optional image shown behind the section content. "
            "Use a large image for best results."
        )
    )

    background_fit = models.CharField(
        max_length=10,
        choices=BACKGROUND_FIT_CHOICES,
        default='cover',
        help_text=(
            "How the background image is sized: "
            "• Cover = fill area, crop if needed; "
            "• Contain = fit inside, no crop (may leave gaps); "
            "• Natural = use image’s intrinsic size; "
            "• Stretch = force to fill width & height (may distort)."
        ),
    )

    background_position_x = models.CharField(
        max_length=6,
        choices=[('left', 'Left'), ('center', 'Center'), ('right', 'Right')],
        default='center',
        help_text="Horizontal focal point used when the image is cropped (Left/Center/Right).",
    )

    background_position_y = models.CharField(
        max_length=6,
        choices=[('top', 'Top'), ('center', 'Center'), ('bottom', 'Bottom')],
        default='center',
        help_text="Vertical focal point used when the image is cropped (Top/Center/Bottom).",
    )

    section_height_mode = models.CharField(
        max_length=12,
        choices=HEIGHT_MODE_CHOICES,
        default='auto',
        help_text=(
            "Height behavior: "
            "Auto = height grows with content; "
            "Fixed (px) = use min-height in pixels; "
            "Viewport (vh) = use min-height as % of viewport height."
        ),
    )

    section_height_value = models.PositiveIntegerField(
        default=40,
        verbose_name='Min section height',
        help_text=(
            "Numeric height value used when mode is Fixed (px) or Viewport (vh). "
            "Applied as min-height (e.g., 60 -> 60px or 60vh). Ignored when mode is Auto."
        ),
    )

    enable_border = models.BooleanField(
        default=True,
        help_text="Draw a separator line below this section."
    )

    border_color = ColorField(
        null=True,
        blank=True,
        default=None,
        help_text="Separator color. Leave blank to use the theme’s accent color."
    )

    full_width = models.BooleanField(
        default=False,
        help_text='Enable this if you want the section to be full-width'
    )

    def __str__(self):
        return self.name

    def bg_size_css(self) -> str:
        return {
            'cover': 'cover',
            'contain': 'contain',
            'natural': 'auto',
            'stretch': '100% 100%',
        }.get(self.background_fit, 'cover')

    def bg_position_css(self) -> str:
        return f'{self.background_position_x} {self.background_position_y}'

    def min_height_css(self) -> str:
        """Return a min-height CSS fragment or empty when auto."""
        if self.section_height_mode == 'auto':
            return ''
        unit = 'px' if self.section_height_mode == 'fixed_px' else 'vh'
        return f'min-height: {self.section_height_value}{unit};'
