# coding=utf-8

from django.contrib import admin
from example.models import (
    ExampleCollectionRecord,
    RockCollectionRecord
)

admin.site.register(ExampleCollectionRecord)
admin.site.register(RockCollectionRecord)
