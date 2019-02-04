from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class FishFormView(TemplateView):
    """View for fish form"""
    template_name = 'fish_form_page.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('site_id', None)
        return super(FishFormView, self).get(request, *args, **kwargs)
