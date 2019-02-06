# coding=utf-8
"""Search process model definition.

"""
import os
import re
import json
import errno
import urlparse
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

CLUSTER_GENERATION = 'cluster_generation'
SEARCH_RESULTS = 'search_results'
SITES_SUMMARY = 'sites_summary'
TAXON_SUMMARY = 'taxon_summary'

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
        (TAXON_SUMMARY, 'Taxon Summary'),
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
    search_raw_query = models.TextField(
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        super(SearchProcess, self).save(*args, **kwargs)
        return

    def set_search_raw_query(self, raw_query):
        raw_query_converted = re.sub(
            r'(\()(%)([a-zA-Z0-9_ ]+)(%)(\))',
            '(\'%' + r'\3' + '%\')',
            str(raw_query))
        raw_query_converted = re.sub(
            r'(BETWEEN)( )(\d+-\d+-\d+)( )(AND)( )(\d+-\d+-\d+)',
            'BETWEEN \'' + r'\3' + '\' AND \'' + r'\7' + '\'',
            raw_query_converted
        )
        self.search_raw_query = raw_query_converted

        query_parsed = urlparse.urlparse(self.query)
        parameters = urlparse.parse_qs(query_parsed.query)
        for param in parameters:
            queries = parameters[param]
            for query in queries:
                if query[0] == '[' and query[len(query) - 1] == ']':
                    query = query[1:-1]
                for query_splitted in query.split('","'):
                    query_splitted = query_splitted.replace('"', '')
                    self.search_raw_query = (
                        self.search_raw_query.replace(
                            query_splitted,
                            '\'' + query_splitted + '\''
                        )
                    )
        self.save()

    def set_status(self, value, should_save_to_file=True):
        if value == SEARCH_FINISHED:
            self.finished = True
            self.save()
        if not should_save_to_file:
            return
        status = {
            'status': value,
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
