import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.core.mail import send_mail
from django.db import connection
from django.db.models import Q, Count

from preferences import preferences

logger = logging.getLogger("bims")


def _get_boundary_geom() -> GEOSGeometry:
    site_boundary = preferences.SiteSetting.site_boundary
    if not site_boundary:
        raise ValueError("Site boundary not configured in Site Setting.")
    geom = getattr(site_boundary, "geometry", None) or getattr(site_boundary, "geom", None)
    if geom is None:
        raise ValueError("Boundary object has no geometry field (expected 'geometry' or 'geom').")
    try:
        if geom.srid and geom.srid != 4326:
            geom = geom.transform(4326, clone=True)
    except Exception:  # noqa
        pass
    return geom


def _outside_sites_qs(boundary_geom, location_site_obj):
    outside_q = (
        (Q(geometry_point__isnull=False) & ~Q(geometry_point__within=boundary_geom))
        | (Q(geometry_line__isnull=False) & ~Q(geometry_line__within=boundary_geom))
        | (Q(geometry_polygon__isnull=False) & ~Q(geometry_polygon__within=boundary_geom))
        | (Q(geometry_multipolygon__isnull=False) & ~Q(geometry_multipolygon__within=boundary_geom))
    )
    return location_site_obj.objects.filter(outside_q)


def _mail_superusers(subject: str, body: str):
    superusers = (
        get_user_model()
        .objects.filter(is_superuser=True, email__isnull=False)
        .values_list("email", flat=True)
    )
    if superusers:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=list(superusers),
            fail_silently=True,
        )


@shared_task(name="bims.tasks.prune_outside_boundary_gbif", queue="update")
def prune_outside_boundary_gbif(dry_run: bool = False, delete_empty_sites: bool = True) -> dict:
    """
    Delete GBIF occurrences outside the configured site boundary,
    then remove empty Surveys, and optionally delete empty Sites
    that are outside the boundary.

    In dry_run, return hypothetical counts using the same keys.
    """
    from bims.models import Survey, BiologicalCollectionRecord
    from bims.models.location_site import LocationSite
    from tenants.models import Domain

    tenant = getattr(connection, "tenant", None)
    tenant_name = getattr(tenant, "name", "") or getattr(tenant, "schema_name", "") or ""
    domain_name = Domain.objects.filter(tenant__name=tenant_name).first()
    if not domain_name:
        domain_name = tenant_name
    else:
        domain_name = domain_name.domain

    try:
        boundary_geom = _get_boundary_geom()
    except ValueError as e:
        msg = f"[{domain_name}] Outside-boundary cleanup aborted: {e}"
        logger.warning(msg)
        _mail_superusers(
            subject=f"[{domain_name}] Outside-boundary cleanup aborted",
            body=str(e),
        )
        return {"ok": False, "error": str(e)}

    outside_sites = _outside_sites_qs(boundary_geom, LocationSite).values_list("id", "site_code")
    outside_site_ids = [sid for sid, _ in outside_sites]
    outside_site_codes = [scode or "" for _, scode in outside_sites]

    gbif_occ_qs = BiologicalCollectionRecord.objects.filter(
        site_id__in=outside_site_ids,
        source_collection__icontains="gbif",
    )

    gbif_occ_deleted = 0
    surveys_deleted = 0
    sites_deleted = 0

    if not dry_run:
        _total_rows, occ_detail = gbif_occ_qs.delete()
        gbif_occ_deleted = occ_detail.get("bims.BiologicalCollectionRecord", 0)

        empty_surveys_qs = (
            Survey.objects.filter(site_id__in=outside_site_ids)
            .annotate(n_occ=Count("biological_collection_record"))
            .filter(n_occ=0)
        )
        _total_rows, svy_detail = empty_surveys_qs.delete()
        surveys_deleted = svy_detail.get("bims.Survey", 0)

        if delete_empty_sites:
            empty_sites_qs = (
                LocationSite.objects.filter(id__in=outside_site_ids)
                .annotate(
                    n_occ=Count("biological_collection_record"),
                    n_svy=Count("survey"),
                )
                .filter(n_occ=0, n_svy=0)
            )
            _total_rows, site_detail = empty_sites_qs.delete()
            sites_deleted = site_detail.get("bims.LocationSite", 0)
    else:
        gbif_occ_deleted = gbif_occ_qs.count()

        gbif_svy_ids = set(
            Survey.objects.filter(site_id__in=outside_site_ids).values_list("id", flat=True)
        )
        svy_with_non_gbif = set(
            BiologicalCollectionRecord.objects
            .filter(survey_id__in=gbif_svy_ids)
            .exclude(source_collection__icontains="gbif")
            .values_list("survey_id", flat=True)
        )
        would_be_empty = gbif_svy_ids - svy_with_non_gbif
        surveys_deleted = len(would_be_empty)

        if delete_empty_sites:
            site_ids_with_non_gbif = set(
                BiologicalCollectionRecord.objects
                .filter(site_id__in=outside_site_ids)
                .exclude(source_collection__icontains="gbif")
                .values_list("site_id", flat=True)
            )
            sites_deleted = len(set(outside_site_ids) - site_ids_with_non_gbif)

    counts_after = {
        "outside_sites": len(outside_site_ids),
        "gbif_occ_deleted": gbif_occ_deleted,
        "surveys_deleted": surveys_deleted,
        "sites_deleted": sites_deleted,
        "sample_outside_site_codes": outside_site_codes[:20],
        "dry_run": dry_run,
    }

    subject = f"[{domain_name}] Outside-boundary GBIF cleanup{' (DRY RUN)' if dry_run else ''}"
    message = (
        f"Automatic cleanup completed{' (DRY RUN – no changes made)' if dry_run else ''}.\n\n"
        f"• Sites outside boundary     : {counts_after['outside_sites']}\n"
        f"• GBIF occurrences deleted   : {counts_after['gbif_occ_deleted']}\n"
        f"• Surveys deleted            : {counts_after['surveys_deleted']}\n"
        f"• Sites deleted              : {counts_after['sites_deleted']}\n"
        f"• Sample site codes          : {', '.join(counts_after['sample_outside_site_codes']) or '-'}\n"
    )
    _mail_superusers(subject=subject, body=message)

    logger.info(message.replace("\n", " "))
    return {"ok": True, **counts_after}
