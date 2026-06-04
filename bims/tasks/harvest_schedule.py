# bims/tasks.py (replace run_scheduled_gbif_harvest with this)
import datetime as dt
import zlib
from contextlib import contextmanager
from django.db import connection, transaction
from django.utils import timezone
from celery import shared_task
from django.core.files.base import ContentFile
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


def _tenant_lock_keys(schema_name: str, module_group_id: int) -> tuple[int, int]:
    tkey = zlib.crc32(schema_name.encode("utf-8"))
    return _to_signed_int32(tkey), _to_signed_int32(module_group_id)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    soft_time_limit=50*60,
    time_limit=55*60,
    queue="update",
)
def run_scheduled_gbif_harvest(self, schema_name: str, schedule_id: int):
    """Create a HarvestSession and enqueue the correct child job, but never overlap per schedule."""
    from bims.models.harvest_schedule import HarvestSchedule
    from bims.models.harvest_session import HarvestSession
    from bims.tasks import harvest_gbif_species, harvest_collections

    Tenant = get_tenant_model()
    with schema_context(get_public_schema_name()):
        if not Tenant.objects.filter(schema_name=schema_name).exists():
            return {"status": "missing_tenant", "schema_name": schema_name}

    with schema_context(schema_name):
        temp_k1, temp_k2 = _tenant_lock_keys(schema_name, schedule_id)
        with pg_advisory_lock(temp_k1, temp_k2):

            with transaction.atomic():
                sched = (HarvestSchedule.objects
                         .select_for_update()
                         .select_related("module_group")
                         .get(id=schedule_id))

                if not sched.enabled:
                    return {"status": "disabled"}

                open_session = (HarvestSession.objects
                                .filter(schedule=sched, finished=False, canceled=False)
                                .order_by("-start_time")
                                .first())
                if open_session:
                    return {
                        "status": "skipped_open_session",
                        "schema": schema_name,
                        "open_session_id": open_session.id,
                        "started_at": open_session.start_time.isoformat(),
                    }

                now = timezone.now()
                since = sched.last_harvest_until or (now - dt.timedelta(days=7))
                until = now

                parent_species = sched.parent_species or sched.module_group.gbif_parent_species

                session = HarvestSession.objects.create(
                    harvester=None,
                    module_group=sched.module_group,
                    parent_species=parent_species,
                    start_time=now,
                    category="gbif",
                    finished=False,
                    canceled=False,
                    is_fetching_species=getattr(sched, "is_fetching_species", False),
                    harvest_synonyms=sched.harvest_synonyms_default,
                    boundary=sched.boundary_default,
                    status="queued",
                    schedule=sched,
                    trigger="scheduled",
                    since_time=since,
                    until_time=until,
                )

            session.log_file.save(
                f"{schema_name}-harvest-{session.id}.log",
                ContentFile(
                    f"[{timezone.now().isoformat()}] "
                    f"Queued {'species' if session.is_fetching_species else 'occurrences'} job\n"
                )
            )

            if session.is_fetching_species:
                harvest_gbif_species.delay(session.id, schema_name=schema_name)
                job = "species"
            else:
                harvest_collections.delay(session.id, resume=True, chunk_size=250, schema_name=schema_name)
                job = "occurrences"

            return {
                "status": "enqueued",
                "job": job,
                "schema": schema_name,
                "session_id": session.id,
                "since": since.isoformat(),
                "until": until.isoformat(),
            }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    soft_time_limit=50 * 60,
    time_limit=55 * 60,
    queue="update",
)
def run_scheduled_bims_harvest(self, schema_name: str, schedule_id: int):
    """Create a BIMS HarvestSession and enqueue harvest_bims_species for a scheduled run."""
    from bims.models.harvest_schedule import HarvestSchedule
    from bims.models.harvest_session import HarvestSession
    from bims.tasks.harvest_bims_species import harvest_bims_species

    Tenant = get_tenant_model()
    with schema_context(get_public_schema_name()):
        if not Tenant.objects.filter(schema_name=schema_name).exists():
            return {"status": "missing_tenant", "schema_name": schema_name}

    with schema_context(schema_name):
        temp_k1, temp_k2 = _tenant_lock_keys(schema_name, schedule_id)
        with pg_advisory_lock(temp_k1, temp_k2) as locked:
            if not locked:
                return {"status": "lock_not_acquired", "schema": schema_name}

            sched = HarvestSchedule.objects.select_related("module_group").get(id=schedule_id)

            if not sched.enabled:
                return {"status": "disabled"}

            bims_config = sched.bims_config or {}
            base_url = (bims_config.get("base_url") or "").strip()
            remote_group_id = bims_config.get("remote_group_id")

            if not base_url or not remote_group_id:
                return {"status": "missing_bims_config", "schedule_id": schedule_id}

            open_session = (
                HarvestSession.objects.filter(schedule=sched, finished=False, canceled=False)
                .order_by("-start_time")
                .first()
            )
            if open_session:
                return {
                    "status": "skipped_open_session",
                    "schema": schema_name,
                    "open_session_id": open_session.id,
                }

            now = timezone.now()
            session = HarvestSession.objects.create(
                harvester=None,
                module_group=sched.module_group,
                start_time=now,
                category="bims",
                is_fetching_species=True,
                finished=False,
                canceled=False,
                schedule=sched,
                trigger="scheduled",
                status="queued",
                additional_data={
                    "base_url": base_url,
                    "remote_group_id": int(remote_group_id),
                    "remote_group_name": bims_config.get("remote_group_name", ""),
                    "import_mode": "existing",
                    "mark_readonly": False,
                },
            )

            session.log_file.save(
                f"{schema_name}-bims-harvest-{session.id}.log",
                ContentFile(
                    f"[{now.isoformat()}] Scheduled BIMS harvest queued "
                    f"(group={sched.module_group_id}, remote={remote_group_id})\n"
                ),
            )

            harvest_bims_species.delay(session.id, schema_name=schema_name)

            return {
                "status": "enqueued",
                "schema": schema_name,
                "session_id": session.id,
                "base_url": base_url,
                "remote_group_id": remote_group_id,
            }
