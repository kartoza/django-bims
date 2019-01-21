from django.views.generic import ListView
from sass.models.sass5_sheet import SASS5Sheet


class SassListView(ListView):

    template_name = 'sass_list_page.html'
    context_object_name = 'sass_5_sheet'
    paginate_by = 10
    ordering = ['-date']

    def get_queryset(self):
        return SASS5Sheet.objects.filter(
            owner=self.request.user
        )
