from django.contrib.gis.db import models


class SiteVisitEcologicalCondition(models.Model):

    site_visit = models.ForeignKey(
        'sass.SiteVisit',
        null=False,
        on_delete=models.CASCADE
    )

    sass_score = models.IntegerField(
        null=True,
        blank=True
    )

    aspt_score = models.FloatField(
        null=True,
        blank=True
    )

    ecological_condition = models.ForeignKey(
        'sass.SassEcologicalCategory',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
