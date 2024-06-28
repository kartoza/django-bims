import requests
import os
import time
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.conf import settings
from django.core.cache import cache


class MiniSASSObservationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        file_path = os.path.join(settings.MEDIA_ROOT, 'observations_data.json')
        cache_timeout = 60 * 60 * 24
        data = None

        if os.path.exists(file_path):
            file_age = os.path.getmtime(file_path)
            if (time.time() - file_age) < cache_timeout:
                with open(file_path, 'r') as file:
                    data = json.load(file)

        if data:
            return Response(data)

        url = "https://minisass.sta.do.kartoza.com/monitor/observations/"
        token = ""
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
