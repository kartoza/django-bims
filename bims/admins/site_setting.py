from django import forms
from django.utils.translation import gettext_lazy as _
from preferences.admin import PreferencesAdmin

from bims.models.site_setting import SiteSetting

SECRET_INPUTS = [
    'recaptcha_secret_key',
    'iucn_api_key',
    'cites_token_api',
    'virtual_museum_token',
    'resend_api_key',
    'github_feedback_token',
    'gbif_password'
]


class SiteSettingAdminForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = '__all__'

    recaptcha_secret_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    iucn_api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    cites_token_api = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    virtual_museum_token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    resend_api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    github_feedback_token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    minisass_token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(SiteSettingAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            for secret_input in SECRET_INPUTS:
                self.fields[secret_input].widget.attrs['placeholder'] = '******'
                self.fields[secret_input].required = False


class SiteSettingAdmin(PreferencesAdmin):
    form = SiteSettingAdminForm

    readonly_fields = ("gbif_excluded_project_ids_effective_display",)

    fieldsets = (
        (_("General"), {
            "fields": (
                "site_notice",
                "default_data_source",
                "default_site_name",
                "site_code_generator",
                "github_repo_path",
                "copyright_text",
            ),
            "classes": ("wide",),
        }),
        (_("Landing & Docs"), {
            "fields": (
                "landing_page_partners_title",
                "blog_page_link",
                "docs_page_link",
                "homepage_redirect_url",
            ),
            "classes": ("collapse",),
        }),
        (_("Map"), {
            "fields": (
                "default_basemap",
                "default_center_map",
                "default_extent_map",
                "map_min_zoom",
                "spatial_filter_layer_style",
                "map_default_filters",
                "default_location_site_cluster",
                "geoserver_location_site_layer",
                "show_third_party_layer",
            ),
        }),
        (_("Boundary & Park Layers"), {
            "fields": (
                "base_country_code",
                "boundary_key",
                "site_boundary",
                "park_wfs_url",
                "park_wfs_layer_name",
                "park_wfs_attribute_key",
                "park_layer",
                "park_layer_csv",
                "section_layer_csv",
            ),
        }),
        (_("Uploads & Templates"), {
            "fields": (
                "readme_download",
                "taxonomic_upload_template",
                "occurrence_upload_template",
                "auto_validate_taxa_on_upload",
            ),
        }),
        (_("Features / Toggles"), {
            "fields": (
                "enable_sass",
                "enable_water_temperature",
                "enable_ecosystem_type",
                "enable_download_request_approval",
                "show_module_summary_on_dashboard",
                "enable_remove_all_occurrences_tool",
                "allow_taxa_edit_in_admin",
            ),
            "classes": ("collapse",),
        }),
        (_("External Integrations & Tokens"), {
            "fields": (
                "github_feedback_repo",
                "github_feedback_token",
                "recaptcha_site_key",
                "recaptcha_secret_key",
                "minisass_token",
                "iucn_api_key",
                "cites_token_api",
                "virtual_museum_token",
                "resend_api_key",
                "default_from_email",
            ),
            "classes": ("collapse",),
        }),
        (_("Pesticide Dashboard"), {
            "fields": ("pesticide_quaternary_data_file",),
            "classes": ("collapse",),
        }),
        (_("GBIF"), {
            "fields": (
                "gbif_username",
                "gbif_password",
                "gbif_excluded_project_ids",
                "gbif_excluded_project_ids_effective_display"
            ),
        }),
    )

    def gbif_excluded_project_ids_effective_display(self, obj):
        """
        Read-only view of the effective exclusions:
        CSV from admin + tenant defaults (e.g. 'fbis' on FBIS tenant).
        """
        if not obj:
            return ""
        vals = getattr(obj, "gbif_excluded_project_ids_effective", []) or []
        return ", ".join(vals) if vals else "(none)"

    gbif_excluded_project_ids_effective_display.short_description = _(
        "Excluded projectIds (effective)"
    )

    def save_model(self, request, obj, form, change):
        if change:
            for secret_input in SECRET_INPUTS:
                if secret_input in form.changed_data:
                    setattr(obj, secret_input, form.cleaned_data[secret_input])
                else:
                    current_value = getattr(obj, secret_input)
                    setattr(obj, secret_input, current_value)
        obj.save()

    class Media:
        js = ("admin/js/sitesetting_sections.js",)
