from rest_framework import serializers
from td_biblio.models import Entry


class ReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for cluster model.
    """
    journal = serializers.SerializerMethodField()
    journal_abbreviation = serializers.SerializerMethodField()

    def get_journal(self, obj):
        return obj.journal.name

    def get_journal_abbreviation(self, obj):
        return obj.journal.abbreviation

    class Meta:
        model = Entry
        fields = '__all__'
