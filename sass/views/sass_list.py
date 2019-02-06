from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from sass.models.site_visit import SiteVisit


class SassListView(ListView):

    template_name = 'sass_list_page.html'
    context_object_name = 'site_visits'
    paginate_by = 50
    ordering = ['site_visit_date']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SassListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SiteVisit.objects.all().order_by('-site_visit_date')
