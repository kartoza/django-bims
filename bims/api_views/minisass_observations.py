import requests
import os
import json

from preferences import preferences
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.conf import settings


class MiniSASSObservationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            'observations_data.json')
        data = None

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)

        if data:
            return Response(data)

        url = "https://minisass.org/monitor/observations/"
        token = preferences.SiteSetting.minisass_token
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            with open(file_path, 'w') as file:
                json.dump(data, file)
            return Response(data)
        else:
            return Response(
                response.text,
                status=response.status_code)
