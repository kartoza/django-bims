from django.urls import path
from pesticide.views import PesticideDashboardView

urlpatterns = [
    path('pesticide-dashboard/<int:site_id>/',
         PesticideDashboardView.as_view(),
         name='pesticide-dashboard')
]
