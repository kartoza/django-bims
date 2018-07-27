# coding=utf-8
from braces.views import LoginRequiredMixin
from django.contrib.auth import logout


class ValidatorRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        validator = \
            'validator' in request.user.groups.all().values_list(
                'groupprofile__categories__name', flat=True)

        if request.user.is_authenticated() and not validator:
            logout(request)
            return self.handle_no_permission(request)
        elif not request.user.is_authenticated():
            return self.handle_no_permission(request)

        return super(ValidatorRequiredMixin, self).dispatch(
            request, *args, **kwargs)
