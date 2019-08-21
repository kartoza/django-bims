from rest_framework import serializers
from td_biblio.models.bibliography import (
    Author, Editor, Entry, Journal, Publisher)


class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer author bibliography.
    """

    class Meta:
        model = Author
        exclude = []


class EditorSerializer(serializers.ModelSerializer):
    """
    Serializer editor bibliography.
    """

    class Meta:
        model = Editor
        exclude = []


class JournalSerializer(serializers.ModelSerializer):
    """
    Serializer journal bibliography.
    """

    class Meta:
        model = Journal
        exclude = []


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer publisher bibliography.
    """

    class Meta:
        model = Publisher
        exclude = []


class EntrySerializer(serializers.ModelSerializer):
    """
    Serializer entry bibliography.
    """
    full_title = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    editors = serializers.SerializerMethodField()
    journal = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()

    def get_full_title(self, obj):
        return obj.__unicode__()

    def get_authors(self, obj):
        return AuthorSerializer(obj.authors.all(), many=True).data

    def get_editors(self, obj):
        return EditorSerializer(obj.editors.all(), many=True).data

    def get_journal(self, obj):
        return JournalSerializer(obj.journal).data

    def get_publisher(self, obj):
        return PublisherSerializer(obj.publisher).data

    class Meta:
        model = Entry
        exclude = []
