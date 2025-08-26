from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ordered_model.admin import OrderedModelAdmin

from bims_theme.models.font import CustomFont


class DynamicCKEditorUploadingWidget(CKEditorUploadingWidget):
    def __init__(self, *args, dynamic_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        if dynamic_config:
            self.config.update(dynamic_config)


class CustomCKEditorAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        fonts = list(CustomFont.objects.filter(is_active=True).order_by("order", "name"))
        font_names = [
            f"{f.name}/{f.stack.strip() or f.name.strip()}" for f in fonts
        ]
        font_names += [
            "Arial/Arial, Helvetica, sans-serif",
            "Georgia/Georgia, serif",
            "Times New Roman/'Times New Roman', Times, serif",
            "Courier New/'Courier New', Courier, monospace",
            "Verdana/Verdana, Geneva, sans-serif",
        ]
        contents_css = [f.css_url for f in fonts if f.css_url]
        field = form.base_fields["content"]
        field.widget = DynamicCKEditorUploadingWidget(
            config_name="default",
            dynamic_config={
                "toolbar": "Custom",
                "allowedContent": True,
                "extraPlugins": "font,colorbutton,justify",
                "font_names": ";".join(font_names) + ";",
                "contentsCss": contents_css,
            },
        )

        return form
