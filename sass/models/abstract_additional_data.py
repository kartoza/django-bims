import json
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder


class AbstractAdditionalData(models.Model):

    additional_data = JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        default=dict,
    )

    def save(self, *args, **kwargs):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        while not is_dictionary and attempt < max_allowed:
            if not self.additional_data:
                break
            if isinstance(self.additional_data, dict):
                is_dictionary = True
            else:
                self.additional_data = json.loads(self.additional_data)
                attempt += 1
        super(AbstractAdditionalData, self).save(*args, **kwargs)

    class Meta:
        abstract = True
