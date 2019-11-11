import logging

from datetime import timedelta

from django import forms
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.timezone import now

from bims.models import Visitor, Pageview
from bims.conf import TRACK_PAGEVIEWS
from bims.models import Taxonomy, BiologicalCollectionRecord, LocationSite

log = logging.getLogger(__file__)

# tracking wants to accept more formats than default, here they are
input_formats = [
    '%Y-%m-%d %H:%M:%S',    # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M',       # '2006-10-25 14:30'
    '%Y-%m-%d',             # '2006-10-25'
    '%Y-%m',                # '2006-10'
    '%Y',                   # '2006'
]


class DashboardForm(forms.Form):
    start = forms.DateTimeField(required=False, input_formats=input_formats)
    end = forms.DateTimeField(required=False, input_formats=input_formats)


@staff_member_required()
def dashboard(request):
    """Counts, aggregations and more!"""
    end_time = now()
    start_time = end_time - timedelta(days=7)
    defaults = {'start': start_time, 'end': end_time}

    form = DashboardForm(data=request.GET or defaults)
    if form.is_valid():
        start_time = form.cleaned_data['start']
        end_time = form.cleaned_data['end']

    # determine when tracking began
    try:
        obj = Visitor.objects.order_by('start_time')[0]
        track_start_time = obj.start_time
    except (IndexError, Visitor.DoesNotExist):
        track_start_time = now()

    # If the start_date is before tracking began, warn about incomplete data
    warn_incomplete = (start_time < track_start_time)

    # queries take `date` objects (for now)
    user_stats = Visitor.objects.user_stats(start_time, end_time)
    visitor_stats = Visitor.objects.stats(start_time, end_time)
    if TRACK_PAGEVIEWS:
        pageview_stats = Pageview.objects.stats(start_time, end_time)
    else:
        pageview_stats = None

    taxon_count = Taxonomy.objects.count()
    collections_count = \
        BiologicalCollectionRecord.objects.filter(validated=True).count()
    location_site_count = LocationSite.objects.all().count()

    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'user_stats': user_stats,
        'visitor_stats': visitor_stats,
        'pageview_stats': pageview_stats,
        'taxon_count': taxon_count,
        'collections_count': collections_count,
        'location_site_count': location_site_count,
    }
    return render(request, 'tracking/dashboard.html', context)
