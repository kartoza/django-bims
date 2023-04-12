from django.urls import path
from pesticide.views import PesticideDashboardView
from pesticide.api_views import DownloadPesticideByQuaternary

urlpatterns = [
    path('pesticide-by-quaternary/<str:quaternary_id>/',
         DownloadPesticideByQuaternary.as_view(),
         name='download-pesticide-by-quaternary'),
    path('pesticide-dashboard/<int:site_id>/',
         PesticideDashboardView.as_view(),
         name='pesticide-dashboard')
]
