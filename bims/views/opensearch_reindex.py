from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django_tenants.utils import get_public_schema_name, schema_context

from bims.models.opensearch_reindex import OpenSearchReindexRun


class OpenSearchReindexView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView,
):
    template_name = 'opensearch_reindex.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with schema_context(get_public_schema_name()):
            runs = list(
                OpenSearchReindexRun.objects.prefetch_related(
                    'tenant_statuses'
                )[:20]
            )
        context['runs'] = runs
        context['active_run'] = next(
            (run for run in runs if run.status == OpenSearchReindexRun.RUNNING),
            None,
        )
        return context
