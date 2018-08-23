from django.conf.urls import url
from reports.views.kbims_report import view_pdf

urlpatterns = [
    url(r'^report/', view_pdf, name='report'),
]
