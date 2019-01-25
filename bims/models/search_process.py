# coding=utf-8
"""Search process model definition.

"""
import os
import json
import errno
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

CLUSTER_GENERATION = 'cluster_generation'
SEARCH_RESULTS = 'search_results'
SITES_SUMMARY = 'sites_summary'

SEARCH_PROCESSING = 'processing'
SEARCH_FINISHED = 'finished'
SEARCH_FAILED = 'failed'


class SearchProcess(models.Model):
    """Search process model
    """
    SEARCH_TYPE = (
        (CLUSTER_GENERATION, 'Cluster Generation'),
        (SEARCH_RESULTS, 'Search Results'),
        (SITES_SUMMARY, 'Site Summary'),
    )

    file_path = models.CharField(
        blank=True,
        max_length=250,
    )
    category = models.CharField(
        max_length=50,
        choices=SEARCH_TYPE,
        blank=False
    )
    query = models.CharField(
        max_length=2000,
        blank=False
    )
    process_id = models.CharField(
        max_length=200,
        blank=True
    )
    finished = models.BooleanField(
        default=False
    )

    def set_status(self, value, should_save_to_file=True):
        if value == SEARCH_FINISHED:
            self.finished = True
            self.save()
        if not should_save_to_file:
            return
        status = {
            'current_status': value,
            'process': self.process_id
        }
        self.save_to_file(results=status)

    def save_to_file(self, results):
        """
        Save dictionary results to file
        :param results: dictionary
        """
        with open(self.file_path, 'wb') as status_file:
            status_file.write(json.dumps(results))

    def get_file_if_exits(self, finished=True):
        if os.path.exists(self.file_path) and self.finished == finished:
            raw_data = open(self.file_path)
            return json.load(raw_data)
        else:
            self.finished = False
            self.save()
        return None

    def set_process_id(self, process_id):
        self.process_id = process_id
        path_folder = os.path.join(settings.MEDIA_ROOT, self.category)
        try:
            os.mkdir(path_folder)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass
        self.file_path = os.path.join(path_folder, process_id)
        self.save()


@receiver(pre_delete, sender=SearchProcess)
def searchprocess_delete(sender, instance, **kwargs):
    import os
    if os.path.exists(instance.file_path):
        os.remove(instance.file_path)
