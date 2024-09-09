from rest_framework import serializers

from bims.models import Taxonomy
from bims.serializers.taxon_serializer import TaxonSerializer


class TaxonDetailSerializer(TaxonSerializer):
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    subfamily = serializers.SerializerMethodField()
    tribe = serializers.SerializerMethodField()
    subtribe = serializers.SerializerMethodField()
    subgenus = serializers.SerializerMethodField()

    species_group = serializers.SerializerMethodField()
    subspecies = serializers.SerializerMethodField()

    def get_kingdom(self, obj: Taxonomy):
        return obj.kingdom_name

    def get_phylum(self, obj: Taxonomy):
        return obj.phylum_name

    def get_class_name(self, obj: Taxonomy):
        return obj.class_name

    def get_order(self, obj: Taxonomy):
        return obj.order_name

    def get_subfamily(self, obj: Taxonomy):
        return obj.sub_family_name

    def get_tribe(self, obj: Taxonomy):
        return obj.tribe_name

    def get_subtribe(self, obj: Taxonomy):
        return obj.sub_tribe_name

    def get_species_group(self, obj: Taxonomy):
        return ''

    def get_subspecies(self, obj: Taxonomy):
        sub_species_name = obj.sub_species_name
        if sub_species_name:
            genus_name = obj.genus_name
            if genus_name:
                sub_species_name = sub_species_name.replace(genus_name, '', 1).strip()
            species_name = self.get_species(obj)
            if species_name:
                sub_species_name = sub_species_name.replace(species_name, '', 1).strip()
        return sub_species_name

    def get_subgenus(self, obj: Taxonomy):
        return obj.sub_genus_name
