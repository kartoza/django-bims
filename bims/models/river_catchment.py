from django.db import models


class RiverCatchment(models.Model):
    parent = models.ForeignKey(
        verbose_name='Parent',
        to='self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    key = models.CharField(
        blank=False,
        null=False,
        max_length=100
    )

    value = models.CharField(
        blank=False,
        null=False,
        max_length=100
    )

    def __str__(self):
        return '%s - %s' % (
            self.key,
            self.value
        )
