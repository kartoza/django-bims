import csv
import io
import json

from braces.views import SuperuserRequiredMixin
from django.http import Http404, HttpResponse
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response

from bims.models import (
    BiologicalCollectionRecord,
    DecisionSupportTool
)


class DecisionSupportToolList(APIView):
    """API for listing all decision support tools."""

    def get(self, request, *args):
        dst = DecisionSupportTool.objects.all().values_list(
            'name', flat=True
        ).order_by('name').distinct('name')
        return HttpResponse(
            json.dumps(list(dst)),
            content_type='application/json'
        )


class DecisionSupportToolView(SuperuserRequiredMixin, APIView):

    def post(self, request):
        dst_file = request.FILES.get('dst_file', None)
        errors = []
        created = 0

        if not dst_file:
            raise Http404('Missing csv file!')

        decoded_file = dst_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)

        line_count = 0
        for line in csv.reader(io_string, delimiter=','):
            if line_count == 0:
                print(f'Column names are {", ".join(line)}')
                line_count += 1
            else:
                uuid = line[0].replace('\n', '').strip()
                name = line[1].replace('\n', '').strip()
                try:
                    bio = BiologicalCollectionRecord.objects.get(
                        uuid=uuid
                    )
                except BiologicalCollectionRecord.DoesNotExist:
                    errors.append(f'{line_count} '
                                  f': {uuid} Collection Record not found.')
                    continue

                try:
                    dst, dst_created = (
                        DecisionSupportTool.objects.get_or_create(
                            biological_collection_record=bio,
                            name=name
                        )
                    )
                except DecisionSupportTool.MultipleObjectsReturned:
                    continue

                if dst_created:
                    created += 1

                print(
                    f'\t{uuid} DST for {name}')
                line_count += 1

        if created > 0:
            messages.add_message(request, messages.INFO,
                                 f'{created} records added.')
        else:
            messages.add_message(request, messages.INFO,
                                 f'No records added.')
        if errors:
            messages.add_message(
                request,
                messages.ERROR,
                f'Total error : {len(errors)}'
            )
            messages.add_message(
                request,
                messages.ERROR,
                '\n'.join(errors[:10])
            )
        return Response({
            'Done': True
        })
