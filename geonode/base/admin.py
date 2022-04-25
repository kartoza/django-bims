# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.contrib import admin
from django.conf import settings

from dal import autocomplete
from taggit.forms import TagField

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from dal_select2_taggit.widgets import TaggitSelect2

from geonode.base.models import (
    TopicCategory,
    SpatialRepresentationType,
    Region,
    RestrictionCodeType,
    License,
    HierarchicalKeyword,
)


class LicenseAdmin(admin.ModelAdmin):
    model = License
    list_display = ('id', 'name')
    list_display_links = ('name',)


class TopicCategoryAdmin(admin.ModelAdmin):
    model = TopicCategory
    list_display_links = ('identifier',)
    list_display = (
        'identifier',
        'description',
        'gn_description',
        'fa_class',
        'is_choice')
    if settings.MODIFY_TOPICCATEGORY is False:
        exclude = ('identifier', 'description',)

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False


class RegionAdmin(admin.ModelAdmin):
    model = Region
    list_display_links = ('name',)
    list_display = ('code', 'name', 'parent')
    search_fields = ('code', 'name',)
    group_fieldsets = True


class SpatialRepresentationTypeAdmin(admin.ModelAdmin):
    model = SpatialRepresentationType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False


class RestrictionCodeTypeAdmin(admin.ModelAdmin):
    model = RestrictionCodeType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False


class HierarchicalKeywordAdmin(TreeAdmin):
    search_fields = ('name', )
    form = movenodeform_factory(HierarchicalKeyword)


admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(HierarchicalKeyword, HierarchicalKeywordAdmin)


class TaggitSelect2Custom(TaggitSelect2):
    """Overriding Select2 tag widget for taggit's TagField.
       Fixes error in tests where 'value' is None.
    """

    def value_from_datadict(self, data, files, name):
        """Handle multi-word tag.

        Insure there's a comma when there's only a single multi-word tag,
        or tag "Multi word" would end up as "Multi" and "word".
        """

        try:
            value = super(TaggitSelect2Custom, self).value_from_datadict(data, files, name)
            if value and ',' not in value:
                value = '%s,' % value
            return value
        except TypeError:
            return ""


class ResourceBaseAdminForm(autocomplete.FutureModelForm):

    keywords = TagField(widget=TaggitSelect2Custom('autocomplete_hierachical_keyword'))

    class Meta:
        pass
