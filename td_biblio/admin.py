# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import (Author, Editor, Journal, Publisher, Entry, Collection,
                     AuthorEntryRank)


class AuthorEntryRankInline(admin.TabularInline):
    extra = 1
    model = AuthorEntryRank
    ordering = ('rank',)


class AbstractHumanAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
    ordering = ('last_name', 'first_name')


class AuthorAdmin(AbstractHumanAdmin):
    list_display = ('last_name', 'first_name', 'user')
    raw_id_fields = ('user',)


class EditorAdmin(AbstractHumanAdmin):
    raw_id_fields = ('user',)


class AbstractEntityAdmin(admin.ModelAdmin):
    ordering = ('name',)


class JournalAdmin(AbstractEntityAdmin):
    pass


class PublisherAdmin(AbstractEntityAdmin):
    pass


class EntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'publication_date'
    fieldsets = (
        ('Publication core fields', {
            'fields': ('type', 'title', 'journal',
                       ('volume', 'number'),
                       ('pages', ),
                       ('publication_date',
                        'is_partial_publication_date'),
                       'url')
        }),
        ('Identifiers', {
            'fields': (('doi', 'issn'), ('isbn', 'pmid'))
        }),
        ('Book fields', {
            'fields': ('booktitle', 'edition', 'chapter')
        }),
        ('PhD Thesis', {
            'fields': ('school',)
        }),
        ('Proceedings', {
            'fields': ('organization',)
        }),
        ('Miscellaneous', {
            'fields': ('editors', 'publisher', 'address', 'annote', 'note')
        }),
        ('Cross References', {
            'fields': ('crossref',)
        }),
    )
    inlines = (AuthorEntryRankInline,)
    list_display = ('title', 'first_author', 'type', 'publication_date',
                    'journal')
    list_filter = ('publication_date', 'journal', 'authors')
    list_per_page = 20
    list_select_related = True
    ordering = ('-publication_date',)
    raw_id_fields = ('authors', 'crossref')
    search_fields = ('title',)


class CollectionAdmin(admin.ModelAdmin):

    def size(self, obj):
        """Get the number of entries in each collection"""
        return obj.entries.count()

    list_display = ('name', 'size')
    raw_id_fields = ('entries',)


admin.site.register(Author, AuthorAdmin)
admin.site.register(Editor, EditorAdmin)
admin.site.register(Journal, JournalAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Collection, CollectionAdmin)
