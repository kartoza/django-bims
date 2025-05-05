from django.contrib.auth.mixins import AccessMixin
from preferences import preferences


class TaxaAccessMixin(AccessMixin):
    """Grant access to the taxa page if the user is authenticated or if public access is enabled."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not preferences.SiteSetting.is_public_taxa:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
