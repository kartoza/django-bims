from rest_framework.views import Response
from rest_framework.decorators import api_view
from bims.serializers.bio_collection_serializer import (
    BioCollectionSerializer,
    BioCollectionOneRowSerializer
)
from bims.models.biological_collection_record import BiologicalCollectionRecord


@api_view(['GET'])
def get_latest_bio(request):
    bios = BiologicalCollectionRecord.objects.all().order_by('-id')
    serializer = BioCollectionSerializer(bios, many=True)
    return Response(serializer.data[:10])
