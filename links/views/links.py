from ..models.links import Category
from django.views.generic import ListView


class LinksCategoryView(ListView):
    """Returns all  link categories."""

    template_name = 'links/links.html'
    context_object_name = 'categories'
    paginate_by = 10
    queryset = Category.objects.all()

    def get_context_data(self, **kwargs):
        """Create context variables for use in templates."""
        context = super(LinksCategoryView, self).get_context_data()
        context['categories'] = self.queryset
        return context
