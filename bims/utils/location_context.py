import logging
import operator
import os
from functools import reduce
from typing import Optional, Iterable, List

from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.db.models.fields.related import ForeignObjectRel

from bims.cache import HARVESTING_GEOCONTEXT, set_cache
from bims.models.spatial_scale import SpatialScale
from bims.models.spatial_scale_group import SpatialScaleGroup
from bims.models.location_site import LocationSite, generate_site_code
from bims.models.location_context import LocationContext
from bims.utils.logger import log

from bims.models.geocontext_setting import GeocontextSetting

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def array_to_dict(array, key_name='key'):
    dictionary = {}
    if not isinstance(array, list):
        return dictionary
    for data_dict in array:
        try:
            for data_key, data_value in data_dict.iteritems():
                if isinstance(data_value, list):
                    formatted_dict = array_to_dict(data_value)
                    if formatted_dict:
                        data_dict[data_key] = formatted_dict
                elif data_value:
                    if isinstance(data_value, float):
                        continue
                    if data_value.isdigit():
                        data_dict[data_key] = int(data_value)
                    else:
                        try:
                            data_dict[data_key] = float(data_value)
                        except ValueError:
                            continue
                else:
                    continue
            dictionary[data_dict[key_name]] = data_dict
        except (AttributeError, KeyError, TypeError):
            continue
    return dictionary


def process_spatial_scale_data(location_context_data, group=None):
    for context_group_value in location_context_data:
        try:
            context_group = location_context_data[context_group_value]
        except TypeError:
            return
        if 'value' in context_group:
            if not context_group['value']:
                continue
            spatial_type = 'select'
            spatial_query = context_group['value']
            spatial_scale_group, created = (
                SpatialScaleGroup.objects.get_or_create(
                    key=context_group['key'],
                    name=context_group['name'],
                    parent=group
                ))
            try:
                SpatialScale.objects.get_or_create(
                    group=spatial_scale_group,
                    key=context_group['key'],
                    name=context_group['name'],
                    type=spatial_type,
                    query=spatial_query
                )
            except SpatialScale.MultipleObjectsReturned:
                # shouldn't be happen
                spatial_scales = SpatialScale.objects.filter(
                    group=spatial_scale_group,
                    key=context_group['key'],
                    name=context_group['name'],
                    type=spatial_type,
                    query=spatial_query
                )
                SpatialScale.objects.filter(
                    id__in=spatial_scales.values_list('id', flat=True)[1:]
                ).delete()
        else:
            spatial_scale_group, created = (
                SpatialScaleGroup.objects.get_or_create(
                    key=context_group['key'],
                    name=context_group['name'],
                    parent=group
                ))
            if 'service_registry_values' in context_group:
                process_spatial_scale_data(
                    context_group['service_registry_values'],
                    group=spatial_scale_group
                )


def _prepare_group_keys(raw_keys: Optional[Iterable[str]]) -> List[str]:
    """Return a clean list of group keys without attribute suffixes.
    """
    if not raw_keys:
        geocontext_setting = GeocontextSetting.objects.first()
        raw_keys = (
            geocontext_setting.geocontext_keys.split(",")
            if geocontext_setting and geocontext_setting.geocontext_keys
            else []
        )
    elif not isinstance(raw_keys, list):
        raw_keys = str(raw_keys).split(",")
    raw_keys = [k.strip() for k in raw_keys if k and k.strip()]
    return raw_keys


def _init_file_logger() -> logging.Logger:
    """Create a tenant-aware ``FileHandler`` if it has not been added yet."""
    tenant_name = str(connection.schema_name)
    log_file_name = f"{tenant_name}_get_location_context_data.log"
    log_file_path = os.path.join(settings.MEDIA_ROOT, log_file_name)

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    open(log_file_path, "a").close()

    if not any(
        isinstance(h, logging.FileHandler) and h.baseFilename == log_file_path
        for h in logger.handlers
    ):
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_location_context_data(
    *,
    group_keys: Optional[Iterable[str]] = None,
    site_id: Optional[str] = None,
    only_empty: bool = False,
    should_generate_site_code: bool = False,
) -> None:
    """Harvest GeoContext data **per context** instead of **per site**.

    Parameters
    ----------
    group_keys
        The GeoContext group keys to harvest. May be an iterable or a single
        comma-separated string.  If ``None`` or empty, the keys defined in
        :class:`~bims.models.GeocontextSetting` will be used.
    site_id
        Limit the harvesting to a subset of sites (comma-separated list of
        ``LocationSite.id``).  When *None*, all sites will be considered.
    only_empty
        If *True*, only harvest sites that do not yet contain the requested
        context.  This minimises unnecessary API calls.
    should_generate_site_code
        When harvesting succeeds and a site is missing ``site_code``, generate
        one using :func:`bims.utils.site_code.generate_site_code`.
    """
    _init_file_logger()
    _log = logger.info

    if site_id:
        location_sites = LocationSite.objects.filter(id__in=str(site_id).split(","))
    else:
        location_sites = LocationSite.objects.all()

    raw_keys = _prepare_group_keys(group_keys)
    if not raw_keys:
        _log("No GeoContext group keys provided or configured – nothing to do.")
        return

    key_map = {k.split(":")[0]: k for k in raw_keys}

    _log(
        "Starting GeoContext harvesting in 'per-context' mode: %s groups, %s sites",
        len(key_map),
        location_sites.count(),
    )

    for query_key, full_key in key_map.items():
        if only_empty:
            sites_for_group = location_sites.exclude(
                locationcontext__group__geocontext_group_key=query_key
            )
        else:
            sites_for_group = location_sites

        total = sites_for_group.count()
        if total == 0:
            _log("All sites already contain context '%s' – skipping.", query_key)
            continue

        _log("Harvesting context '%s' for %d site(s).", query_key, total)

        for idx, site in enumerate(sites_for_group, start=1):
            _log("[%s/%s] [SITE %s] Adding context '%s'", idx, total, site.id, full_key)
            success, message = site.add_context_group(full_key)
            status = "SUCCESS" if success else "FAILED"
            _log("[%s] [SITE %s] [%s] %s", status, site.id, full_key, message)

            if should_generate_site_code and not site.site_code:
                scode, _ = generate_site_code(site, lat=site.latitude, lon=site.longitude)
                site.site_code = scode
                site.save(update_fields=["site_code"])
                _log("Generated site code '%s' for site %s", scode, site.id)

    set_cache(HARVESTING_GEOCONTEXT, False)
    _log("GeoContext harvesting completed.")


def merge_context_group(excluded_group=None, group_list=None):
    """
    Merge multiple location context groups
    """
    if not excluded_group:
        return
    if not group_list:
        return
    groups = group_list.exclude(id=excluded_group.id)

    if groups.count() < 1:
        return

    log('Merging %s data' % groups.count())

    links = [
        rel.get_accessor_name() for rel in excluded_group._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for group in groups:
            log('----- {} -----'.format(str(group)))
            for link in links:
                try:
                    objects = getattr(group, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for : {taxon}'.format(
                            obj=str(objects.model._meta.label),
                            taxon=str(group)
                        ))
                        update_dict = {
                            getattr(group, link).field.name: excluded_group
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            log(''.join(['-' for i in range(len(str(group)) + 12)]))

    groups.delete()
