import requests
from datetime import datetime
from celery import shared_task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.core.management import call_command
from django_tenants.utils import get_tenant_model, schema_context

logger = get_task_logger(__name__)


@shared_task(name='bims.tasks.import_data_task', bind=True, queue='update')
def import_data_task(self, module, limit=10):
    from bims.models.import_task import ImportTask
    from preferences import preferences

    current_month = datetime.now().month
    current_year = datetime.now().year

    TenantModel = get_tenant_model()
    tenants = TenantModel.objects.all().exclude(schema_name='public')
    for tenant in tenants:
        with schema_context(tenant.schema_name):
            api_token = preferences.SiteSetting.virtual_museum_token
            if not api_token:
                logger.info(f"No virtual museum token found for {tenant.schema_name}.")
                continue
            try:
                # Check for in-progress tasks
                running_tasks = ImportTask.objects.filter(
                    module=module,
                    in_progress=True)
                for task in running_tasks:
                    result = AsyncResult(task.celery_task_id)
                    if result.status in ['STARTED', 'RETRY']:
                        logger.info(f"Found a running task for {module} : {result.status}, skipping new task.")
                        return

                # Check if a task was completed this month
                last_task = ImportTask.objects.filter(
                    module=module, in_progress=False
                ).order_by('-updated_at').first()
                if (
                        last_task and
                        last_task.updated_at.month == current_month and
                        last_task.updated_at.year == current_year
                ):
                    logger.info(f"Task for {module} has already been completed this month.")
                    return

                # Create or resume a task
                task = ImportTask.objects.filter(module=module, in_progress=True).first()
                if not task:
                    # No in-progress task, create a new one
                    if module == 'odonates':
                        url = (
                            f'https://api.birdmap.africa/vmus/v2/dwc/'
                            f'OdonataMAP/{api_token}/all/json/0'
                        )
                    elif module == 'anurans':
                        url = (
                            f'https://api.birdmap.africa/vmus/v2/dwc/'
                            f'FrogMAP/{api_token}/all/json/0'
                        )

                    response = requests.get(url)
                    response.raise_for_status()
                    total_records = int(
                        response.json()['data']['result'][0]['Number_of_records']
                    )
                    task = ImportTask.objects.create(
                        module=module,
                        total_records=total_records,
                        start_index=0,
                        in_progress=True,
                        log_text='',
                        celery_task_id=self.request.id
                    )
                else:
                    total_records = int(task.total_records)
                    task.celery_task_id = self.request.id
                    task.save()

                start_index = int(task.start_index)

                while start_index < total_records:
                    task = ImportTask.objects.get(id=task.id)
                    self.update_state(state='STARTED',
                                      meta={'process': 'Harvesting virtual museum data'})

                    if task.cancel:
                        cancel_log = f"Task for {module} in schema {tenant.schema_name} was cancelled.\n"
                        logger.info(cancel_log)
                        task.log_text += cancel_log
                        task.in_progress = False
                        task.save()
                        break

                    if start_index + limit > total_records:
                        limit = total_records - start_index

                    log_text = (
                        f"Fetching {module} data: {start_index},{limit} of {total_records} - "
                        f"{datetime.today()} in schema {tenant.schema_name}\n"
                    )
                    logger.info(log_text)
                    task.log_text += log_text
                    task.save()

                    if module == 'odonates':
                        call_command('import_odonata_data',
                                     start_index=start_index,
                                     limit=limit,
                                     module_name='Invertebrates',
                                     token=api_token)
                    elif module == 'anurans':
                        call_command('import_frog_vm_data',
                                     start_index=start_index,
                                     limit=limit,
                                     module_name='Anurans',
                                     token=api_token)

                    task.refresh_from_db()
                    start_index += limit
                    task.start_index = start_index
                    task.save()

                    if task.log_text.count('\n') > 10:
                        task.log_text = '\n'.join(task.log_text.split('\n')[-10:])
                        task.save()

                if not task.cancel:
                    task.in_progress = False
                    task.save()
            except requests.exceptions.RequestException as e:
                error_log = f"Request error: {e} in schema {tenant.schema_name}\n"
                logger.error(error_log)
                if task:
                    task.log_text += error_log
                    task.save()
                self.retry(exc=e, countdown=60 * 5)
            except Exception as e:
                error_log = f"Unexpected error: {e} in schema {tenant.schema_name}\n"
                logger.error(error_log)
                if task:
                    task.log_text += error_log
                    task.in_progress = False
                    task.save()
                raise
