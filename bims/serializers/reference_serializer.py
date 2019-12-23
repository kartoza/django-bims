from rest_framework import serializers
from td_biblio.models import Entry


class ReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for cluster model.
    """
    journal = serializers.SerializerMethodField()
    journal_abbreviation = serializers.SerializerMethodField()

    def get_journal(self, obj):
        if obj.journal:
            return obj.journal.name
        return '-'

    def get_journal_abbreviation(self, obj):
        if obj.journal:
            return obj.journal.abbreviation
        return '-'

    class Meta:
        model = Entry
        fields = '__all__'
