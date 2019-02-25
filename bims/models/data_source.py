from django.contrib.gis.db import models


class DataSource(models.Model):
    """Data source for forms"""

    name = models.CharField(
        null=False,
        blank=False,
        max_length=200
    )

    category = models.CharField(
        null=True,
        blank=True,
        max_length=100
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        if self.category:
            return '{name} - {category}'.format(
                name=self.name,
                category=self.category
            )
        return self.name
