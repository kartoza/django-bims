import zlib
from contextlib import contextmanager
from django.db import connection, transaction
from django.utils import timezone
from celery import shared_task
from django_tenants.utils import schema_context, get_public_schema_name, get_tenant_model


@contextmanager
def pg_advisory_lock(key1: int, key2: int):
    with connection.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s, %s)", [key1, key2])
        locked = cur.fetchone()[0]
    try:
        yield locked
    finally:
        if locked:
            with connection.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s, %s)", [key1, key2])


def _to_signed_int32(val: int) -> int:
    """Convert unsigned 32-bit int to signed 32-bit int for PostgreSQL."""
    val = val & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val


def _tenant_lock_keys(schema_name: str, publish_id: int) -> tuple[int, int]:
    tkey = zlib.crc32(f"gbif_publish_{schema_name}".encode("utf-8"))
    return _to_signed_int32(tkey), _to_signed_int32(publish_id)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=30*60,
    time_limit=35*60,
    queue="update",
)
def run_scheduled_gbif_publish(self, schema_name: str, publish_id: int):
    """
    Execute a scheduled GBIF publish job.

    Publishes occurrence data to GBIF using the configuration specified
    in the GbifPublish schedule.
    """
    from bims.models.gbif_publish import GbifPublish

    Tenant = get_tenant_model()
    with schema_context(get_public_schema_name()):
        if not Tenant.objects.filter(schema_name=schema_name).exists():
            return {"status": "missing_tenant", "schema_name": schema_name}

    with schema_context(schema_name):
        temp_k1, temp_k2 = _tenant_lock_keys(schema_name, publish_id)
        with pg_advisory_lock(temp_k1, temp_k2) as locked:
            if not locked:
                return {
                    "status": "skipped_locked",
                    "schema": schema_name,
                    "publish_id": publish_id,
                }

            with transaction.atomic():
                publish_schedule = (
                    GbifPublish.objects
                    .select_for_update()
                    .select_related("module_group", "gbif_config")
                    .get(id=publish_id)
                )

                if not publish_schedule.enabled:
                    return {"status": "disabled"}

                if not publish_schedule.gbif_config:
                    return {"status": "no_config", "publish_id": publish_id}

                if not publish_schedule.gbif_config.is_active:
                    return {"status": "config_inactive", "publish_id": publish_id}

                config = publish_schedule.gbif_config
                module_group = publish_schedule.module_group

                from bims.utils.gbif_publish import publish_gbif_data_with_config

                try:
                    result = publish_gbif_data_with_config(
                        config=config,
                        module_group=module_group,
                    )

                    publish_schedule.last_publish = timezone.now()
                    publish_schedule.save(update_fields=["last_publish"])

                    return {
                        "status": "success",
                        "schema": schema_name,
                        "publish_id": publish_id,
                        "module_group": module_group.name if module_group else None,
                        "dataset_key": result.get("dataset_key"),
                        "records_published": result.get("records_published", 0),
                    }

                except Exception as e:
                    return {
                        "status": "error",
                        "schema": schema_name,
                        "publish_id": publish_id,
                        "error": str(e),
                    }
