# -*- coding: utf-8 -*-

from django.db import models, connection
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from colorfield.fields import ColorField
from bims_theme.models.carousel_header import CarouselHeader
from bims_theme.models.partner import Partner
from django.contrib.sites.models import Site


THEME_CACHE_KEY = 'bims_theme'


class CustomTheme(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Associated Site",
        help_text="The site this taxon group is associated with."
    )
    name = models.CharField(
        max_length=100,
        help_text='Will not appear anywhere'
    )
    description = models.TextField(
        null=True,
        help_text='Will not appear anywhere',
        blank=True
    )
    site_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='The name of the site'
    )
    logo = models.ImageField(
        upload_to='site_logo',
        null=True,
        blank=True
    )
    navbar_logo = models.ImageField(
        upload_to='navbar_site_logo',
        null=True,
        blank=True
    )
    landing_page_sections = models.ManyToManyField(
        'bims_theme.LandingPageSection',
        null=True,
        blank=True,
        help_text='Landing page sections'
    )
    carousels = models.ManyToManyField(
        'bims_theme.CarouselHeader',
        null=True,
        blank=True,
        help_text='Carousels that will appear on the landing page'
    )
    partners_section_title = models.CharField(
        max_length=100,
        default='PARTNERS',
        help_text='Title for the partners display section'
    )
    partners_section_order = models.PositiveIntegerField(
        default=1,
        help_text='The order of the partners section from the bottom'
    )
    partners = models.ManyToManyField(
        'bims_theme.Partner',
        null=True,
        blank=True,
        help_text='List of partners that will appear on the landing page'
    )
    partners_section_background_color = ColorField(
        default='#FFFFFF',
        help_text='Background color for the partners section'
    )

    funders_section_title = models.CharField(
        max_length=100,
        default='FUNDERS',
        help_text='Title for the funders display section'
    )
    funders_section_order = models.PositiveIntegerField(
        default=0,
        help_text='The order of the funders section from the bottom'
    )
    funders = models.ManyToManyField(
        'bims_theme.Partner',
        related_name='theme_funders',
        null=True,
        blank=True,
        help_text='Specify funders to be featured on the landing page'
    )
    funders_section_background_color = ColorField(
        default='#FFFFFF',
        help_text='Background color for the funders section'
    )

    menu_items = models.ManyToManyField(
        'bims_theme.MenuItem',
        null=True,
        blank=True,
        help_text='Extra menu items'
    )
    date = models.DateTimeField(
        auto_now_add=True,
        blank=True
    )
    main_accent_color = ColorField(
        default='#18A090'
    )
    secondary_accent_color = ColorField(
        default='#DBAF00'
    )
    main_button_text_color = ColorField(
        default='#FFFFFF'
    )
    navbar_background_color = ColorField(
        default='#343a40'
    )
    navbar_text_color = ColorField(
        default='#FFFFFF'
    )
    is_enabled = models.BooleanField(
        default=True
    )
    is_footer_enabled = models.BooleanField(
        default=False
    )
    facebook_link = models.URLField(
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    twitter_link = models.URLField(
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    instagram_link = models.URLField(
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    email_1 = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    email_2 = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    phone_1 = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    phone_2 = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    address_1 = models.TextField(
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    address_2 = models.TextField(
        blank=True,
        default='',
        help_text='To be displayed in the footer'
    )
    auth_background = models.ImageField(
        blank=True,
        null=True,
        help_text='Background image for login/logout page.'
    )
    footer_background = models.ImageField(
        blank=True,
        null=True,
        help_text='Background image for footer in landing page.'
    )
    hide_site_visit = models.BooleanField(
        default=False,
        help_text='Hide site visit in the landing page'
    )
    location_site_name = models.CharField(
        default='Site',
        help_text=(
            'The name of the location site as it will appear in the dashboard, '
            'on landing pages, and in other user interfaces.'
        )
    )
    location_site_name_plural = models.CharField(
        default='Sites',
        help_text=(
            'The plural form of the location site name for use '
            'when referring to multiple sites.'
        )
    )

    login_modal_logo = models.ImageField(
        blank=True,
        null=True,
        help_text='Optional logo displayed in the login modal.'
    )

    login_modal_title = models.CharField(
        default='Login',
        blank=True,
        max_length=100,
        help_text='Optional title text displayed in the login modal.'
    )

    class Meta:
        ordering = ("date", )
        verbose_name_plural = 'Custom Themes'

    def __str__(self):
        return self.name


@receiver(post_save, sender=CustomTheme)
def disable_other(sender, instance, **kwargs):
    if instance.is_enabled:
        CustomTheme.objects.exclude(
            pk=instance.pk,
        ).update(is_enabled=False)


# Invalidate the cached theme if a partner or a theme is updated.
@receiver(post_save, sender=CustomTheme)
@receiver(post_delete, sender=CustomTheme)
@receiver(post_save, sender=Partner)
@receiver(post_delete, sender=Partner)
@receiver(post_save, sender=CarouselHeader)
@receiver(post_delete, sender=CarouselHeader)
def invalidate_cache(sender, instance, **kwargs):
    tenant = connection.tenant
    try:
        tenant_name = str(tenant.name)
    except AttributeError:
        tenant_name = 'bims'
    cache.delete(THEME_CACHE_KEY + tenant_name)
