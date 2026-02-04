from django.contrib import admin


def _inject_gbif_app(app_list):
    gbif_object_names = {
        "GbifPublishConfigProxy",
        "GbifPublishProxy",
        "GbifPublishSessionProxy",
    }

    for idx, app in enumerate(app_list):
        if app.get("app_label") != "bims":
            continue

        gbif_models = [
            model for model in app.get("models", [])
            if model.get("object_name") in gbif_object_names
        ]
        if not gbif_models:
            return app_list

        app["models"] = [
            model for model in app.get("models", [])
            if model.get("object_name") not in gbif_object_names
        ]

        gbif_app = {
            "name": "GBIF Publishing",
            "app_label": "gbif_publishing",
            "app_url": app.get("app_url"),
            "has_module_perms": app.get("has_module_perms", True),
            "models": gbif_models,
        }
        app_list.insert(idx + 1, gbif_app)
        return app_list

    return app_list


def patch_admin_app_list():
    if getattr(admin.site, "_gbif_app_list_patched", False):
        return

    original_get_app_list = admin.site.get_app_list

    def get_app_list(request, app_label = None):
        app_list = original_get_app_list(request, app_label)
        return _inject_gbif_app(app_list)

    admin.site.get_app_list = get_app_list
    admin.site._gbif_app_list_patched = True


patch_admin_app_list()
