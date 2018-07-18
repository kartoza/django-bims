__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '07/03/17'

import os
import shapefile
import struct
from django.conf import settings

LIMIT_FILE = 20 * 1024 * 1024


class FileExceedLimit(Exception):
    def __init__(self):
        super(FileExceedLimit, self).__init__('File Exceed Limit %s' % LIMIT_FILE)
        self.errors = 'File Exceed Limit %s' % LIMIT_FILE


class FilesHasNotSameName(Exception):
    def __init__(self):
        super(FilesHasNotSameName, self).__init__('Files name has to be same')
        self.errors = 'Files name has to be same'


class BrokenShapefile(Exception):
    def __init__(self):
        super(BrokenShapefile, self).__init__('Shapefile is broken')
        self.errors = 'Shapefile is broken'


class WrongExtention(Exception):
    def __init__(self):
        super(WrongExtention, self).__init__('Wrong Extention')
        self.errors = 'Wrong Extention'


def handle_uploaded_file(f, filename):
    """Handle uploaded file to be saved in temporary file.
    """
    temp_folder = settings.TEMP_FOLDER
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    filename = os.path.join(
        temp_folder, filename)
    with open(filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def extract_shape_file(request=None, shp_file=None, shx_file=None, dbf_file=None):
    """Read this shapefile
    """
    if request:
        shp_file = request.FILES['shp_file']
        shx_file = request.FILES['shx_file']
        dbf_file = request.FILES['dbf_file']

    if shp_file.name.endswith('.shp') and shx_file.name.endswith(
            '.shx') and dbf_file.name.endswith('.dbf'):

        shp_filename, ext = os.path.splitext(shp_file.name)
        shp_filename = shp_filename.split('/')[1]

        # save temporary file
        handle_uploaded_file(shp_file, shp_filename + '.shp')
        handle_uploaded_file(shx_file, shp_filename + '.shx')
        handle_uploaded_file(dbf_file, shp_filename + '.dbf')

        sf = shapefile.Reader(os.path.join(
            settings.TEMP_FOLDER, shp_filename + ".dbf")
        )

        fields = sf.fields[1:]
        field_names = [field[0].lower() for field in fields]

        output = []
        for sr in sf.shapeRecords():
            atr = dict(zip(field_names, sr.record))
            geom = sr.shape.__geo_interface__
            output.append(
                dict(type="Feature", geometry=geom, properties=atr))

        # delete that file
        os.remove(os.path.join(
            settings.TEMP_FOLDER, shp_filename + '.shp')
        )
        os.remove(os.path.join(
            settings.TEMP_FOLDER, shp_filename + '.shx')
        )
        os.remove(os.path.join(
            settings.TEMP_FOLDER, shp_filename + '.dbf')
        )
        return output
    else:
        raise WrongExtention


def get_shapefile_data(shapefile_file):
    """Get shapefile data.

    :returns: A geojson data from shapefile
    :rtype: dict
    """
    try:
        # read the shapefile
        reader = shapefile.Reader(shapefile_file)
        fields = reader.fields[1:]
        field_names = [field[0].lower() for field in fields]
        buffer = []
        date_fields = ['date', 'datum']
        for sr in reader.shapeRecords():
            atr = dict(zip(field_names, sr.record))
            geom = sr.shape.__geo_interface__
            feature = dict(
                type="Feature",
                geometry=geom,
                properties=atr)
            buffer.append(feature)
            try:
                for date_field in date_fields:
                    if date_field in feature['properties'] and feature['properties'][date_field]:
                        feature['properties'][date_field] = \
                            feature['properties'][date_field].strftime('%Y-%m-%d')
            except Exception as e:
                raise e
        return {
            "type": "FeatureCollection",
            "features": buffer
        }
    except (shapefile.ShapefileException,
            struct.error, IOError):
        raise BrokenShapefile