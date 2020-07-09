import csv
import re
import copy
import logging
from django.contrib.sites.models import Site
from bims.scripts.species_keys import *  # noqa
from bims.models import (
    UploadSession
)
logger = logging.getLogger('bims')


class DataCSVUpload(object):
    taxa_upload_session = UploadSession.objects.none()
    error_list = []
    success_list = []
    headers = []
    total_rows = 0
    domain = ''
    csv_dict_reader = None

    def start(self):
        """
        Start processing the csv file from upload session
        """
        self.error_list = []
        self.success_list = []
        self.domain = Site.objects.get_current().domain
        self.total_rows = len(
            self.taxa_upload_session.process_file.readlines()
        ) - 1
        with open(self.taxa_upload_session.process_file.path) as csv_file:
            self.csv_dict_reader = csv.DictReader(csv_file)
            self.process_csv_dict_reader()

    def error_file(self, error_row, error_message):
        """
        Write to error file
        :param error_row: error data
        :param error_message: error message for this row
        """
        logger.log(
            level=logging.ERROR,
            msg=str(error_message)
        )
        error_row['error_message'] = error_message
        self.error_list.append(error_row)

    def success_file(self, success_row, taxon_id):
        """
        Write to success file
        :param success_row: success data
        :param taxon_id: id of the added taxonomy
        """
        success_row['taxon_id'] = 'http://{d}/admin/bims/taxonomy/{id}'.format(
            d=self.domain,
            id=taxon_id
        )
        self.success_list.append(success_row)

    def finish(self):
        """
        Finishing the csv upload process
        """
        if not self.csv_dict_reader:
            return

        headers = self.csv_dict_reader.fieldnames
        file_name = (
            self.taxa_upload_session.process_file.name.replace(
                'taxa-file/', '')
        )
        file_path = (
            self.taxa_upload_session.process_file.path.replace(file_name, '')
        )

        # Create error file
        # TODO : Done it simultaneously with file processing
        if self.error_list:
            error_headers = copy.deepcopy(headers)
            if 'error_message' not in error_headers:
                error_headers.append('error_message')
            if 'link' in error_headers:
                error_headers.remove('link')
            error_file_path = '{path}error_{name}'.format(
                path=file_path,
                name=file_name
            )
            with open(error_file_path, mode='w') as csv_file:
                writer = csv.writer(
                    csv_file, delimiter=',', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow(error_headers)
                for data in self.error_list:
                    data_list = []
                    for key in error_headers:
                        try:
                            data_list.append(data[key])
                        except KeyError:
                            continue
                    writer.writerow(data_list)
            self.taxa_upload_session.error_file.name = (
                'taxa-file/error_{}'.format(
                    file_name
                )
            )

        # Create success file
        # TODO : Done it simultaneously with file processing
        if self.success_list:
            success_headers = copy.deepcopy(headers)
            if 'link' not in success_headers:
                success_headers.append('link')
            if 'error_message' in success_headers:
                success_headers.remove('error_message')
            success_file_path = '{path}success_{name}'.format(
                path=file_path,
                name=file_name
            )
            with open(success_file_path, mode='w') as csv_file:
                writer = csv.writer(
                    csv_file, delimiter=',', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow(success_headers)
                for data in self.success_list:
                    data_list = []
                    for key in success_headers:
                        try:
                            data_list.append(data[key])
                        except KeyError:
                            continue
                    writer.writerow(data_list)
            self.taxa_upload_session.success_file.name = (
                'taxa-file/success_{}'.format(
                    file_name
                )
            )

        self.taxa_upload_session.processed = True
        self.taxa_upload_session.progress = 'Finished'
        self.taxa_upload_session.save()

    @staticmethod
    def row_value(row, key):
        """
        Get row value by key
        :param row: row data
        :param key: key
        :return: row value
        """
        row_value = ''
        try:
            row_value = row[key]
            row_value = row_value.replace('\xa0', ' ')
            row_value = row_value.replace('\xc2', '')
            row_value = row_value.replace('\\xa0', '')
            row_value = row_value.strip()
            row_value = re.sub(' +', ' ', row_value)
        except KeyError:
            pass
        return row_value

    def process_csv_dict_reader(self):
        """
        Read and process data from csv file
        """
        index = 1
        for row in self.csv_dict_reader:
            logger.debug(row)
            self.taxa_upload_session.progress = '{index}/{total}'.format(
                index=index,
                total=self.total_rows
            )
            self.taxa_upload_session.save()
            index += 1
            self.process_row(row=row)

        self.finish()

    def process_row(self, row):
        """ Processing row of the csv files """
        raise NotImplementedError(
            'DataCSVUpload subclass must implement process_row')
