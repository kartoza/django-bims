# coding=utf-8

from django.contrib import admin
from django import forms
from django.conf import settings
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ordered_model.admin import OrderedModelAdmin

from bims.admins.custom_ckeditor_admin import CustomCKEditorAdmin
from bims_theme.models import (
    CustomTheme,
    CarouselHeader,
    Partner,
    LandingPageSection,
    LandingPageSectionContent,
    MenuItem
)
from bims_theme.models.font import CustomFont


class CustomThemeAdmin(admin.ModelAdmin):
    fieldsets = (
        ("General", {
            "fields": ("name", "description", "site_name", "logo", "is_enabled")
        }),
        ("Navbar", {
            "fields": (
                "navbar_logo",
                "navbar_background_color",
                "navbar_text_color",
                "navbar_custom_typography_enabled",
                "navbar_font",
                "navbar_font_size_px",
                "navbar_font_weight",
                "navbar_letter_spacing_em",
                "navbar_text_case",
                "navbar_brand_divider_enabled"
            )
        }),
        ("Landing Page", {
            "fields": ("landing_page_sections", "carousels", "hide_site_visit")
        }),
        ("Summary Dashboard", {
            "fields": ("landing_page_occurrence_records_title",
                       "landing_page_occurrence_records_title_font",
                       "landing_page_occurrence_records_title_font_size_px",
                       "landing_page_occurrence_records_title_font_weight",
                       "landing_page_occurrence_records_title_text_color",
                       "summary_font", "summary_font_size_px",
                       "summary_text_color", "summary_background_color",
                       "summary_text_case", "show_explore_map")
        }),
        ("Partners & Funders", {
            "fields": (
                "partners_section_title", "partners_section_title_font",
                "partners_section_title_font_weight", "partners_section_title_text_color",
                "partners_section_order",
                "partners", "partners_section_background_color",
                "funders_section_title", "funders_section_order",
                "funders", "funders_section_background_color",
            )
        }),
        ("Colors & Buttons", {
            "fields": (
                "main_accent_color", "secondary_accent_color", "main_button_text_color",
            )
        }),
        ("Footer", {
            "fields": (
                "is_footer_enabled", "footer_background",
                "facebook_link", "twitter_link", "instagram_link",
                "email_1", "email_2", "phone_1", "phone_2",
                "address_1", "address_2",
            )
        }),
        ("Auth / Misc", {
            "fields": ("auth_background", "login_modal_logo", "login_modal_title",
                       "location_site_name", "location_site_name_plural", "menu_items")
        }),
    )
    filter_horizontal = ("landing_page_sections", "carousels", "partners", "funders", "menu_items")
    list_display = ("name", "site", "is_enabled", "date")


class CarouselHeaderAdmin(OrderedModelAdmin):
    list_display = ("__str__", "order", "move_up_down_links")
    list_filter = ("banner_fit", "banner_height_mode", "text_alignment")
    search_fields = ("title", "description")
    ordering = ("order",)

    fieldsets = (
        ("Basic", {
            "fields": ("banner", "title", "description")
        }),
        ("Overlay", {
            "fields": ("background_color_overlay", "background_overlay_opacity", "text_color")
        }),
        ("Banner Display", {
            "fields": (
                "banner_fit", "banner_height_mode", "banner_height_value",
                "banner_position_x", "banner_position_y",
                "full_screen_background",
            )
        }),
        ("Title Typography & Position", {
            "fields": (
                "title_font", "title_font_weight",
                "title_letter_spacing_em", "title_font_size",
                "title_alignment", "title_offset_y_percent", "title_line_height_pct",
            )
        }),
        ("Description Typography & Position", {
            "fields": (
                "description_font", "description_font_weight",
                "description_letter_spacing_em", "description_font_size",
                "description_alignment", "description_offset_y_percent", "description_line_height_pct",
            )
        }),
        ("Defaults / Fallbacks", {
            "classes": ("collapse",),
            "fields": ("text_alignment", "text_style"),
        }),
    )


class PartnerAdmin(OrderedModelAdmin):
    list_display = ('order', 'name', 'link', 'move_up_down_links')


class LandingPageSectionAdmin(OrderedModelAdmin):
    list_display = ('name', 'title', 'move_up_down_links')


class LandingPageSectionContentAdmin(CustomCKEditorAdmin):
    pass


class MenuItemAdmin(OrderedModelAdmin):
    list_display = ('title', 'move_up_down_links')


@admin.register(CustomFont)
class CustomFontAdmin(OrderedModelAdmin):
    list_display = ("name", "is_active", "css_url", "move_up_down_links")
    list_editable = ("is_active",)
    search_fields = ("name", "css_url")


admin.site.register(CustomTheme, CustomThemeAdmin)
admin.site.register(CarouselHeader, CarouselHeaderAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(LandingPageSection, LandingPageSectionAdmin)
admin.site.register(LandingPageSectionContent, LandingPageSectionContentAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
