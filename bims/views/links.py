# coding: utf-8
__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'

from django.views.generic import ListView

from bims.models import Category


class LinksCategoryView(ListView):
    """Returns all  link categories."""

    template_name = 'links/links.html'
    paginate_by = 10
    queryset = Category.objects.all()

    def get_context_data(self, **kwargs):
        """Create context variables for use in templates."""
        context = super(LinksCategoryView, self).get_context_data()
        context['categories'] = self.queryset
        return context
