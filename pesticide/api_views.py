import csv
from django.http import HttpResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from preferences import preferences


class DownloadPesticideByQuaternary(APIView):
    """
    API view that generates a downloadable
    report providing estimated crop application rates of each pesticide
    in South Africa for a specified quaternary.

    This view accepts GET requests with a 'quaternary_id' parameter and responds
    with a file containing the pesticide data for the given quaternary.

    Methods:
        get(self, request, *args, **kwargs): Handles the incoming GET request, processes
            the 'quaternary_id' parameter, retrieves the corresponding pesticide data, and
            generates a downloadable report in CSV
    """
    permission_classes = [IsAuthenticated,]

    def get(self, request, quaternary_id):
        csv_key = 'QUATERNARY'
        data = {}

        if not preferences.SiteSetting.pesticide_quaternary_data_file:
            raise Http404()

        with open(
                preferences.SiteSetting.pesticide_quaternary_data_file.path
        ) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if csv_key not in row:
                    raise Http404()
                if row[csv_key] == quaternary_id:
                    data = row

        csv_data =  [[key, value] for key, value in data.items()]
        csv_data = [['Field', 'Value']] + csv_data
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="{quaternary_id}.csv"'
        )
        writer = csv.writer(response)
        for row in csv_data:
            writer.writerow(row)
        return response
