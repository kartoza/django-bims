from django.contrib.gis.db import models


class SiteVisitChem(models.Model):
    site_visit = models.ForeignKey(
        'sass.SiteVisit',
        null=False,
        blank=False
    )

    chem = models.ForeignKey(
        'bims.Chem',
        null=False,
        blank=False
    )

    chem_value = models.FloatField(
        null=True,
        blank=True
    )

    comment = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    max_detectable_limit = models.IntegerField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return '{site_visit} - {chem}'.format(
            site_visit=self.site_visit.location_site.name,
            chem=self.chem.chem_code
        )

    class Meta:
        verbose_name_plural = "Site visit chemistry records"
        verbose_name = "Site visit chemistry record"
