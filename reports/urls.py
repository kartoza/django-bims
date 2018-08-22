from django.conf.urls import url
from reports.views.stats import view_pdf

urlpatterns = [
    url(r'^report/', view_pdf, name='report'),
]
