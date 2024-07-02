from datetime import datetime

from rest_framework import serializers

from bims.models import TaxonGroupTaxonomy, CITESListingInfo
from bims.models.taxonomy import Taxonomy
from bims.serializers.bio_collection_serializer import SerializerContextCache
from bims.models.biological_collection_record import BiologicalCollectionRecord


class ChecklistSerializer(SerializerContextCache):
    """
    Serializer for checklist
    """
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    synonyms = serializers.SerializerMethodField()
    common_name = serializers.SerializerMethodField()
    most_recent_record = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    endemism = serializers.SerializerMethodField()
    global_conservation_status = serializers.SerializerMethodField()
    national_conservation_status = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    cites_listing = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    park_or_mpa_name = serializers.SerializerMethodField()
    creation_date = serializers.SerializerMethodField()
    dataset = serializers.SerializerMethodField()

    def taxon_name_by_rank(
            self,
            obj: Taxonomy,
            rank_identifier: str):
        taxon_name = self.get_context_cache(
            rank_identifier,
            obj.id
        )
        if taxon_name:
            return taxon_name
        taxon_name = obj.__getattribute__(rank_identifier)
        if taxon_name:
            self.set_context_cache(
                rank_identifier,
                obj.id,
                taxon_name
            )
            return taxon_name
        return '-'

    def get_creation_date(self, obj: Taxonomy):
        today = datetime.today()
        return today.strftime('%d/%m/%Y')

    def get_bio_data(self, obj: Taxonomy):
        if not hasattr(self, '_bio_data_cache'):
            self._bio_data_cache = {}
        if obj.id not in self._bio_data_cache:
            bio_records = BiologicalCollectionRecord.objects.filter(taxonomy=obj)
            self._bio_data_cache[obj.id] = bio_records
        return self._bio_data_cache[obj.id]

    def get_taxon_group_taxon_data(self, obj: Taxonomy):
        taxon_group_id = self.context.get('taxon_group_id', None)
        if not taxon_group_id:
            return None
        if not hasattr(self, '_taxon_group_cache'):
            self._taxon_group_cache = {}
        if obj.id not in self._taxon_group_cache:
            taxon_group_taxon = TaxonGroupTaxonomy.objects.filter(
                taxonomy=obj,
                taxongroup_id=taxon_group_id,
                is_validated=True
            ).first()
            if taxon_group_taxon:
                self._taxon_group_cache[obj.id] = taxon_group_taxon
            else:
                return None
        return self._taxon_group_cache[obj.id]

    def get_kingdom(self, obj: Taxonomy):
        return self.taxon_name_by_rank(
            obj,
            'kingdom_name'
        )
    def get_class_name(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'class_name'
        )

    def get_phylum(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'phylum_name'
        )

    def get_order(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'order_name'
        )

    def get_family(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'family_name'
        )

    def get_synonyms(self, obj: Taxonomy):
        synonyms = Taxonomy.objects.filter(
            accepted_taxonomy=obj
        ).values_list('scientific_name', flat=True)
        return ','.join(list(synonyms))

    def get_common_name(self, obj: Taxonomy):
        vernacular_names = list(
            obj.vernacular_names.filter(
                language__istartswith='en').values_list('name', flat=True))
        if len(vernacular_names) == 0:
            return ''
        else:
            return vernacular_names[0]

    def get_most_recent_record(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return ''
        return bio.order_by('collection_date').last().collection_date.year

    def get_dataset(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return ''
        if bio.filter(source_collection__iexact='gbif').exists():
            dataset_names = list(bio.values_list(
                'additional_data__datasetName',
                flat=True
            ))
            dataset_names = [name for name in dataset_names if name is not None]
            if dataset_names:
                return ','.join(set(dataset_names))
        return '-'

    def get_sources(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return ''
        bio = bio.distinct('source_reference')
        try:
            source_data = []
            for collection in bio:
                if collection.source_reference:
                    source_data.append(
                        str(collection.source_reference)
                    )
            return ','.join(source_data)
        except TypeError:
            return ''

    # TODO
    def get_confidence(self, obj: Taxonomy):
        return ''

    # TODO
    def get_park_or_mpa_name(self, obj: Taxonomy):
        return '-'

    def get_origin(self, obj: Taxonomy):
        origin_categories = dict(Taxonomy.CATEGORY_CHOICES)
        taxon_group_taxon = self.get_taxon_group_taxon_data(obj)
        if not taxon_group_taxon:
            taxon_group_taxon = obj
        return (
            origin_categories[taxon_group_taxon.origin]
            if taxon_group_taxon.origin in origin_categories
            else ''
        )

    def get_endemism(self, obj: Taxonomy):
        taxon_group_taxon = self.get_taxon_group_taxon_data(obj)
        if not taxon_group_taxon:
            taxon_group_taxon = obj
        return taxon_group_taxon.endemism.name if taxon_group_taxon.endemism else ''

    def get_global_conservation_status(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.category
        return 'NE'

    def get_national_conservation_status(self, obj):
        if obj.national_conservation_status:
            return obj.national_conservation_status.category
        return ''

    def get_cites_listing(self, obj: Taxonomy):
        cites_listing_info = CITESListingInfo.objects.filter(
            taxonomy=obj
        ).order_by('appendix')
        if cites_listing_info:
            return ','.join(list(cites_listing_info.values_list(
                'appendix', flat=True
            )))
        return ''

    class Meta:
        model = Taxonomy
        fields = [
            'id',
            'kingdom',
            'phylum',
            'class_name',
            'order',
            'family',
            'scientific_name',
            'synonyms',
            'common_name',
            'most_recent_record',
            'origin',
            'endemism',
            'global_conservation_status',
            'national_conservation_status',
            'sources',
            'cites_listing',
            'confidence',
            'park_or_mpa_name',
            'creation_date',
            'dataset'
        ]
