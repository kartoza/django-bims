# models.py
from django.db import models
from django.contrib.flatpages.models import FlatPage


class FlatPageExtension(models.Model):
    flatpage = models.OneToOneField(
        FlatPage,
        on_delete=models.CASCADE,
        related_name='extension')
    show_in_navbar = models.BooleanField(
        default=False,
        verbose_name="Show in Navbar")
    display_order = models.IntegerField(
        default=0,
        verbose_name="Display Order")
    redirect_only = models.BooleanField(
        default=False,
        verbose_name="Redirect Only"
    )

    class Meta:
        verbose_name = "Custom Flat Page"
        verbose_name_plural = "Custom Flat Pages"
        ordering = ['display_order']
