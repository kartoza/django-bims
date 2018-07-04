# coding=utf-8
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.http import Http404


class UserProfileView(TemplateView):
    """View for user profile."""

    template_name = 'user_profile.html'

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        context = super(UserProfileView, self).get_context_data(**kwargs)
        user = self.request.user
        try:
            context['user'] = User.objects.get(username=user)
        except User.DoesNotExist:
            raise Http404()
        return context
