from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Permission
from bims.models.taxonomy import Taxonomy


def user_has_permission_to_validate(user):
    """
    Check if user has permission to validate data
    """
    if user.is_active and user.is_superuser:
        return True
    if user.is_anonymous:
        return False
    return Permission.objects.filter(
            group__user=user,
            codename__contains='can_validate').exists()


class IsValidator(BasePermission):
    """
    Allows access only to validators.
    """
    def has_permission(self, request, view):
        return user_has_permission_to_validate(request.user)


class AllowedTaxon(object):
    """
    Get allowed taxon.
    """
    def get_all_children_taxonomy(self, taxonomy):
        taxonomies = []
        children = taxonomy.get_direct_children()
        if children:
            taxonomies = list(children)
            for taxon in taxonomies:
                taxonomies += self.get_all_children_taxonomy(taxon)
        return taxonomies

    def get(self, user):
        """Return taxon that user has permission to validate."""

        if user.is_active and user.is_superuser:
            return Taxonomy.objects.all()

        all_data_flag = 'data'

        permissions = Permission.objects.filter(
                group__user=user,
                codename__contains='can_validate').values('name')
        allowed_classes = []

        for permission in permissions:
            try:
                class_name = permission['name'].split(' ')[2]
                if class_name.lower() == all_data_flag:
                    return Taxonomy.objects.all()
            except (ValueError, KeyError):
                continue
            allowed_classes.append(class_name)

        taxonomy_classes = Taxonomy.objects.filter(
            scientific_name__in=allowed_classes)

        # Get children taxonomy
        taxa = []
        for taxonomy_class in taxonomy_classes:
            taxa += self.get_all_children_taxonomy(taxonomy_class)

        return taxa
