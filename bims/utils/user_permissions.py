# coding=utf-8
from braces.views import LoginRequiredMixin
from django.http import Http404


class ValidatorRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        validator = \
            'validator' in request.user.groups.all().values_list(
                'groupprofile__categories__name', flat=True)

        if not request.user.is_authenticated():
            return self.handle_no_permission(request)
        elif not validator:
            raise Http404

        return super(ValidatorRequiredMixin, self).dispatch(
            request, *args, **kwargs)
