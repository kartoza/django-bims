from bims.models.biological_collection_record import BiologicalCollectionRecord
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


class SourceReferenceDatabaseAdmin(PolymorphicChildModelAdmin):
    list_display = ('source', 'note')
    base_model = SourceReferenceDatabase


class SourceReferenceDocumentAdmin(PolymorphicChildModelAdmin):
    list_display = ('source', 'note')
    base_model = SourceReferenceDocument


class SourceReferenceAdmin(PolymorphicParentModelAdmin):
    """ The SourceReference """
    base_model = SourceReference
    list_display = (
        'source_reference_title',
        'reference_type',
        'verified',
        'total_records'
    )
    child_models = (
        SourceReferenceBibliography,
        SourceReferenceDatabase,
        SourceReferenceDocument,
        SourceReference
    )
    list_filter = (PolymorphicChildModelFilter,)
    search_fields = (
        'sourcereferencebibliography__source__title',
        'sourcereferencedocument__source__title',
        'sourcereferencedatabase__source__name',
        'source_name',
    )

    def source_reference_title(self, obj):
        try:
            return obj.sourcereferencebibliography.title
        except SourceReferenceBibliography.DoesNotExist:
            pass
        try:
            return obj.sourcereferencedatabase.title
        except SourceReferenceDatabase.DoesNotExist:
            pass
        try:
            return obj.sourcereferencedocument.title
        except SourceReferenceDocument.DoesNotExist:
            pass
        return obj.title

    def reference_type(self, obj):
        try:
            return obj.sourcereferencebibliography.reference_type
        except SourceReferenceBibliography.DoesNotExist:
            pass
        try:
            return obj.sourcereferencedatabase.reference_type
        except SourceReferenceDatabase.DoesNotExist:
            pass
        try:
            return obj.sourcereferencedocument.reference_type
        except SourceReferenceDocument.DoesNotExist:
            pass
        return obj.reference_type

    def total_records(self, obj):
        return BiologicalCollectionRecord.objects.filter(
            source_reference=obj
        ).count()

    source_reference_title.short_description = 'Title'
    reference_type.short_description = 'Reference Type'
    total_records.short_description = 'Total Occurrences'

    actions = ['merge_source_references']

    def merge_source_references(self, request, queryset):

        verified = queryset.filter(verified=True)
        if queryset.count() <= 1:
            self.message_user(
                request, 'Need more than 1 source reference', messages.ERROR
            )
            return

        if not verified.exists():
            self.message_user(
                request, 'Missing verified source reference', messages.ERROR)
            return

        if verified.count() > 1:
            self.message_user(
                request, 'There are more than 1 verified source reference',
                messages.ERROR)
            return

        merge_source_references(primary_source_reference=verified.first(),
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
