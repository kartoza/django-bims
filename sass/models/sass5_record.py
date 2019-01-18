from django.contrib.gis.db import models


class SASS5Record(models.Model):

    sass_sheet = models.ForeignKey(
        'sass.SASS5Sheet',
        verbose_name='SASS Sheet',
        help_text='SASS Sheet',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    taxonomy = models.ForeignKey(
        'bims.Taxonomy',
        verbose_name='Family/Order Taxonomy',
        help_text='Family/Order Taxonomy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    count = models.IntegerField(
        help_text='Count',
        null=True,
        blank=True
    )

    stone_and_rock = models.IntegerField(
        verbose_name='Stone and Rock (S)',
        help_text='Stone and Rock (S)',
        null=True,
        blank=True
    )

    vegetation = models.IntegerField(
        verbose_name='Vegetation (Veg)',
        help_text='Vegetation (Veg)',
        null=True,
        blank=True
    )

    gravel_sand_mud = models.IntegerField(
        verbose_name='Gravel Sand Mud (GSM)',
        help_text='Gravel Sand Mud (GSM)',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'SASS 5 Record'
        verbose_name_plural = 'SASS 5 Records'
