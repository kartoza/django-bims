from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from sass.models.sass5_sheet import SASS5Sheet


class SassListView(ListView):

    template_name = 'sass_list_page.html'
    context_object_name = 'sass_5_sheet'
    paginate_by = 10
    ordering = ['-date']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SassListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SASS5Sheet.objects.filter(
            owner=self.request.user
        )
