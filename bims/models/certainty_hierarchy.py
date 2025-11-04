from django.db import models


class CertaintyHierarchy(models.Model):
    name = models.CharField(max_length=255, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Certainty hierarchy'
        verbose_name_plural = 'Certainty hierarchy'

    def __str__(self):
        return self.nam
