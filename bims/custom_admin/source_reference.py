from django.contrib import admin
from django.contrib import messages

from polymorphic.admin import (
    PolymorphicParentModelAdmin,
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter)
from bims.models.source_reference import (
    DatabaseRecord,
    SourceReference,
    SourceReferenceBibliography,
    SourceReferenceDatabase, SourceReferenceDocument, merge_source_references
)


class DatabaseRecordAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')


class SourceReferenceBibliographyAdmin(PolymorphicChildModelAdmin):
    list_display = ('source', 'note')
    base_model = SourceReferenceBibliography

    actions = ['merge_source_reference_bibliography']

    def merge_source_reference_bibliography(self, request, queryset):
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 source reference bibliography', messages.ERROR
            )
            return
        source_reference = SourceReferenceBibliography.objects.filter(
            id__in=queryset.values_list('id', flat=True)
        ).exclude(id=queryset[0].id)

        source_reference.delete()

    merge_source_reference_bibliography.short_description = 'Merge source reference bibliographys'


class SourceReferenceDatabaseAdmin(PolymorphicChildModelAdmin):
    list_display = ('source', 'note')
    base_model = SourceReferenceDatabase

    actions = ['merge_source_reference_database']

    def merge_source_reference_database(self, request, queryset):
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 source reference database', messages.ERROR
            )
            return
        source_reference = SourceReferenceDatabase.objects.filter(
            id__in=queryset.values_list('id', flat=True)
        ).exclude(id=queryset[0].id)

        source_reference.delete()

    merge_source_reference_database.short_description = 'Merge source reference databases'


class SourceReferenceDocumentAdmin(PolymorphicChildModelAdmin):
    list_display = ('source', 'note')
    base_model = SourceReferenceDocument

    actions = ['merge_source_reference_documents']

    def merge_source_reference_documents(self, request, queryset):

        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 source reference document', messages.ERROR
            )
            return
        source_reference = SourceReferenceDocument.objects.filter(
            id__in=queryset.values_list('id', flat=True)
        ).exclude(id=queryset[0].id)

        source_reference.delete()

    merge_source_reference_documents.short_description = 'Merge source reference documents'


class SourceReferenceAdmin(PolymorphicParentModelAdmin):
    """ The SourceReference """
    base_model = SourceReference
    child_models = (
        SourceReferenceBibliography,
        SourceReferenceDatabase,
        SourceReferenceDocument)
    list_filter = (PolymorphicChildModelFilter,)
    search_fields = (
        'sourcereferencebibliography__source__title',
        'sourcereferencedocument__source__title',
        'sourcereferencedatabase__source__name',
        'source_name'
    )

    actions = ['merge_source_references']

    def merge_source_references(self, request, queryset):

        source_type = queryset.values('polymorphic_ctype').distinct().count()

        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 source reference', messages.ERROR
            )
            return

        elif source_type >= 2:
            self.message_user(
                request, 'Source references should be same type', messages.ERROR
            )
            return

        merge_source_references(primary_source_reference=queryset[0],
                                source_reference_list=queryset)

    merge_source_references.short_description = 'Merge source references'


try:
    admin.site.unregister(DatabaseRecord)
    admin.site.unregister(SourceReferenceBibliography)
    admin.site.unregister(SourceReferenceDatabase)
    admin.site.unregister(SourceReferenceDocument)
    admin.site.unregister(SourceReference)
except Exception:  # noqa
    pass

admin.site.register(DatabaseRecord, DatabaseRecordAdmin)
admin.site.register(
    SourceReferenceBibliography, SourceReferenceBibliographyAdmin)
admin.site.register(SourceReferenceDatabase, SourceReferenceDatabaseAdmin)
admin.site.register(SourceReferenceDocument, SourceReferenceDocumentAdmin)
admin.site.register(SourceReference, SourceReferenceAdmin)
