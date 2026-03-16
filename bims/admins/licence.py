from django.contrib import admin
from bims.models.licence import Licence


@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier", "url")
    search_fields = ("name", "identifier", "url")
