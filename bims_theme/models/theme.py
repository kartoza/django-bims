# -*- coding: utf-8 -*-

from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from colorfield.fields import ColorField
from bims_theme.models.carousel_header import CarouselHeader
from bims_theme.models.partner import Partner


THEME_CACHE_KEY = 'bims_theme'


class CustomTheme(models.Model):
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
    carousels = models.ManyToManyField(
        'bims_theme.CarouselHeader',
        null=True,
        blank=True,
        help_text='Carousels that will appear on the landing page'
    )
    partners = models.ManyToManyField(
        'bims_theme.Partner',
        null=True,
        blank=True,
        help_text='List of partners that will appear on the landing page'
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

    class Meta:
        ordering = ("date", )
        verbose_name_plural = 'Custom Themes'

    def __str__(self):
        return self.name


@receiver(post_save, sender=CustomTheme)
def disable_other(sender, instance, **kwargs):
    if instance.is_enabled:
        CustomTheme.objects.exclude(pk=instance.pk).update(is_enabled=False)


# Invalidate the cached theme if a partner or a theme is updated.
@receiver(post_save, sender=CustomTheme)
@receiver(post_delete, sender=CustomTheme)
@receiver(post_save, sender=Partner)
@receiver(post_delete, sender=Partner)
@receiver(post_save, sender=CarouselHeader)
@receiver(post_delete, sender=CarouselHeader)
def invalidate_cache(sender, instance, **kwargs):
    cache.delete(THEME_CACHE_KEY)
