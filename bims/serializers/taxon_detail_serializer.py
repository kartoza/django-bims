from rest_framework import serializers

from bims.models import Taxonomy
from bims.serializers.taxon_serializer import TaxonSerializer


class TaxonHierarchySerializer(serializers.ModelSerializer):
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    subfamily = serializers.SerializerMethodField()
    tribe = serializers.SerializerMethodField()
    subtribe = serializers.SerializerMethodField()
    subgenus = serializers.SerializerMethodField()

    family = serializers.SerializerMethodField()
    genus = serializers.SerializerMethodField()

    species = serializers.SerializerMethodField()
    species_group = serializers.SerializerMethodField()
    subspecies = serializers.SerializerMethodField()

    def get_species(self, obj: Taxonomy):
        validated = self.context.get('validated', False)
        species_name = ''
        if not validated:
            species_name = obj.species_name
        if obj.hierarchical_data and 'species_name' in obj.hierarchical_data:
            species_name = obj.hierarchical_data['species_name']
        if not species_name:
            species_name = obj.species_name

        if species_name:
            genus_name = self.get_genus(obj)
            if genus_name in species_name:
                try:
                    species_name = (
                        species_name.split(genus_name)[-1].strip()
                    )
                except ValueError:
                    pass

        return species_name

    def get_genus(self, obj: Taxonomy):
        validated = self.context.get('validated', False)
        if not validated:
            return obj.genus_name
        if obj.hierarchical_data and 'genus_name' in obj.hierarchical_data:
            return obj.hierarchical_data['genus_name']
        return obj.genus_name

    def get_family(self, obj: Taxonomy):
        validated = self.context.get('validated', False)
        if not validated:
            return obj.family_name
        if obj.hierarchical_data and 'family_name' in obj.hierarchical_data:
            return obj.hierarchical_data['family_name']
        return obj.family_name

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
        return obj.species_group.name if obj.species_group else ''

    def get_subspecies(self, obj: Taxonomy):
        sub_species_name = obj.sub_species_name
        if not sub_species_name:
            return ''

        genus_name = obj.genus_name
        if genus_name:
            sub_species_name = sub_species_name.replace(
                genus_name, '', 1).strip()
        species_name = self.get_species(obj)
        if species_name:
            sub_species_name = sub_species_name.replace(
                species_name, '', 1).strip()

        return sub_species_name

    def get_subgenus(self, obj: Taxonomy):
        return obj.sub_genus_name


class TaxonDetailSerializer(TaxonSerializer, TaxonHierarchySerializer):
    pass
