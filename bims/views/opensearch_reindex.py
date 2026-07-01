from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
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

    def _get_runs(self):
        with schema_context(get_public_schema_name()):
            return list(
                OpenSearchReindexRun.objects.prefetch_related(
                    'tenant_statuses'
                )[:20]
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        runs = self._get_runs()
        context['runs'] = runs
        context['active_run'] = next(
            (run for run in runs if run.status == OpenSearchReindexRun.RUNNING),
            None,
        )
        return context

    def post(self, request, *args, **kwargs):
        from bims.tasks.opensearch_index import opensearch_reindex

        runs = self._get_runs()
        active = next(
            (r for r in runs if r.status == OpenSearchReindexRun.RUNNING),
            None,
        )
        if active:
            messages.error(request, f'A reindex is already running (run #{active.pk}).')
            return redirect('opensearch-reindex')

        recreate = request.POST.get('recreate') == 'on'
        try:
            chunk_size = int(request.POST.get('chunk_size', 500))
            if chunk_size < 1:
                raise ValueError
        except (ValueError, TypeError):
            chunk_size = 500
        requested_schema = request.POST.get('requested_schema', '').strip()

        with schema_context(get_public_schema_name()):
            run = OpenSearchReindexRun.objects.create(
                status=OpenSearchReindexRun.PENDING,
                recreate=recreate,
                chunk_size=chunk_size,
                requested_schema=requested_schema,
            )

        opensearch_reindex.delay(run.pk)
        messages.success(request, f'Reindex started (run #{run.pk}).')
        return redirect('opensearch-reindex')
