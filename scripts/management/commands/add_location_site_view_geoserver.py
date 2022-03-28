# -*- coding: utf-8 -*-
import requests
import logging
import os
import pycurl
from core.settings.utils import absolute_path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


# call back class for read the data
class DataProvider(object):
    def __init__(self, data):
        self.data = data
        self.finished = False

    def read_cb(self, size):
        assert len(self.data) <= size
        if not self.finished:
            self.finished = True
            return self.data
        else:
            # Nothing more to read
            return ""


# callback class for reading the files
class FileReader:
    def __init__(self, fp):
        self.fp = fp

    def read_callback(self, size):
        return self.fp.read(size)


class Command(BaseCommand):

    username = ''
    password = ''
    service_url = ''
    store_name = 'gis_db'
    workspace = 'bims'
    style_name = 'location_view_style'
    layer_name = 'location_site_view'

    def create_workspace(self):
        """
        Create a new workspace in geoserver, geoserver workspace url
        will be same as name of the workspace
        """
        try:
            url = "{}/rest/workspaces".format(self.service_url)
            data = "<workspace><name>{}</name></workspace>".format(
                self.workspace
            )
            headers = {"content-type": "text/xml"}
            r = requests.post(
                url, data, auth=(self.username, self.password), headers=headers
            )

            if r.status_code == 201:
                return "{} Workspace {} created!".format(r.status_code,
                                                         self.workspace)

            if r.status_code == 401:
                raise Exception("The workspace already exist")

            else:
                raise Exception("The workspace can not be created")

        except Exception as e:
            logger.error("Error: {}\n".format(e))
            return "Error: {}".format(e)

    def create_featurestore(
            self,
            port=5432,
            schema="public",
            overwrite=False,
    ):
        """
        Postgis store for connecting postgres with geoserver
        After creating feature store, you need to publish it
        Input parameters:specify the store name you want to be created,
        the postgis database parameters including host, port, database name,
        schema, user and password,
        """
        try:
            db = os.environ.get("DATABASE_NAME")
            host = os.environ.get("DATABASE_HOST")
            pg_user = os.environ.get("DATABASE_USERNAME")
            pg_password = os.environ.get("DATABASE_PASSWORD")

            c = pycurl.Curl()
            # connect with geoserver
            c.setopt(pycurl.USERPWD, self.username + ":" + self.password)
            c.setopt(
                c.URL,
                "{}/rest/workspaces/{}/datastores".format(self.service_url,
                                                          self.workspace),
            )
            c.setopt(pycurl.HTTPHEADER, ["Content-type: text/xml"])

            # make the connection with postgis database
            database_connection = (
                "<dataStore>"
                "<name>{}</name>"
                "<connectionParameters>"
                "<host>{}</host>"
                "<port>{}</port>"
                "<database>{}</database>"
                "<schema>{}</schema>"
                "<user>{}</user>"
                "<passwd>{}</passwd>"
                "<dbtype>postgis</dbtype>"
                "</connectionParameters>"
                "</dataStore>".format(
                    self.store_name,
                    host, port, db, schema, pg_user, pg_password
                )
            )
            c.setopt(pycurl.POSTFIELDSIZE, len(database_connection))
            c.setopt(pycurl.READFUNCTION,
                     DataProvider(database_connection).read_cb)

            if overwrite:
                c.setopt(pycurl.PUT, 1)
            else:
                c.setopt(pycurl.POST, 1)
            c.perform()
            c.close()
        except Exception as e:
            logger.error("Error:{} \n".format(e))
            return "Error:%s" % str(e)

    def publish_featurestore_sqlview(
        self,
        geom_name="geometry_point",
        geom_type="Point",
    ):
        try:
            name = self.layer_name
            sql = "SELECT * FROM %where%"
            key_column = "site_id"
            default_view = "default_location_site_cluster"

            c = pycurl.Curl()
            layer_xml = """<featureType>
            <name>{0}</name>
            <enabled>true</enabled>
            <namespace>
            <name>{5}</name>
            </namespace>
            <title>{0}</title>
            <srs>EPSG:4326</srs>
            <metadata>
            <entry key="JDBC_VIRTUAL_TABLE">
            <virtualTable>
            <name>{0}</name>
            <sql>{1}</sql>
            <escapeSql>false</escapeSql>
            <keyColumn>{2}</keyColumn>
            <geometry>
            <name>{3}</name>
            <type>{4}</type>
            <srid>4326</srid>
            </geometry>
            <parameter>
            <name>where</name>
            <defaultValue>{6}</defaultValue>
            <regexpValidator>[^;&apos;]+</regexpValidator>
            </parameter>
            </virtualTable>
            </entry>
            </metadata>
            </featureType>""".format(
                name, sql, key_column, geom_name, geom_type, self.workspace,
                default_view
            )
            c.setopt(pycurl.USERPWD, self.username + ":" + self.password)
            c.setopt(
                c.URL,
                "{}/rest/workspaces/{}/datastores/{}/featuretypes".format(
                    self.service_url, self.workspace, self.store_name
                ),
            )
            c.setopt(pycurl.HTTPHEADER, ["Content-type: text/xml"])
            c.setopt(pycurl.POSTFIELDSIZE, len(layer_xml))
            c.setopt(pycurl.READFUNCTION, DataProvider(layer_xml).read_cb)
            c.setopt(pycurl.POST, 1)
            c.perform()
            c.close()
        except Exception as e:
            logger.error("Error: {} \n".format(e))
            return "Error:%s" % str(e)

    def upload_style(
        self, sld_version="1.0.0", overwrite=False
    ):
        """
        The name of the style file will be, sld_name:workspace
        This function will create the style file in a specified workspace.
        Inputs: path to the sld_file, workspace,
        """
        try:
            name = self.style_name

            path = os.path.join(
                absolute_path('scripts', 'static'),
                'data',
                'location_style.sld'
            )

            logger.info(path)

            file_size = os.path.getsize(path)
            url = "{}/rest/workspaces/{}/styles".format(self.service_url,
                                                        self.workspace)

            sld_content_type = "application/vnd.ogc.sld+xml"
            if sld_version == "1.1.0" or sld_version == "1.1":
                sld_content_type = "application/vnd.ogc.se+xml"

            style_xml = "<style><name>{}</name><filename>{}</filename></style>".format(
                name, name + ".sld"
            )
            # create the xml file for associated style
            c = pycurl.Curl()
            c.setopt(pycurl.USERPWD, self.username + ":" + self.password)
            c.setopt(c.URL, url)
            c.setopt(pycurl.HTTPHEADER, ["Content-type:application/xml"])
            c.setopt(pycurl.POSTFIELDSIZE, len(style_xml))
            c.setopt(pycurl.READFUNCTION, DataProvider(style_xml).read_cb)

            if overwrite:
                c.setopt(pycurl.PUT, 1)
            else:
                c.setopt(pycurl.POST, 1)
            c.perform()

            # upload the style file
            c.setopt(c.URL, "{}/{}".format(url, name))
            c.setopt(pycurl.HTTPHEADER, ["Content-type:{}".format(sld_content_type)])
            c.setopt(pycurl.READFUNCTION, FileReader(open(path, "rb")).read_callback)
            c.setopt(pycurl.INFILESIZE, file_size)
            if overwrite:
                c.setopt(pycurl.PUT, 1)
            else:
                c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.UPLOAD, 1)
            c.perform()
            c.close()

        except Exception as e:
            logger.error("Error: {} \n".format(e))
            return "Error: {}".format(e)

    def publish_style(self, content_type="text/xml"):
        """
        publishing a raster file to geoserver
        the coverage store will be created automatically as the same name as the raster layer name.
        input parameters: the parameters connecting geoserver (user,password,
        url and workspace name),the path to the file and file_type indicating it is a geotiff, arcgrid or other raster type
        """

        try:
            c = pycurl.Curl()
            style_xml = (
                "<layer><defaultStyle><name>{}</name></defaultStyle></layer>".format(
                    self.style_name
                )
            )
            c.setopt(pycurl.USERPWD, self.username + ":" + self.password)
            c.setopt(
                c.URL,
                "{}/rest/layers/{}:{}".format(self.service_url, self.workspace, self.layer_name),
            )
            c.setopt(pycurl.HTTPHEADER, ["Content-type: {}".format(content_type)])
            c.setopt(pycurl.POSTFIELDSIZE, len(style_xml))
            c.setopt(pycurl.READFUNCTION, DataProvider(style_xml).read_cb)
            # c.setopt(pycurl.CUSTOMREQUEST, "PUT")
            c.setopt(pycurl.PUT, 1)
            c.perform()
            c.close()
        except Exception as e:
            return "Error: {}".format(e)

    def handle(self, *args, **options):

        self.username = os.environ.get('GEOSERVER_ADMIN_USER', '')
        self.password = os.environ.get('GEOSERVER_ADMIN_PASSWORD', '')
        self.service_url = os.environ.get('GEOSERVER_PUBLIC_LOCATION', '')

        self.create_workspace()
        self.create_featurestore()
        self.publish_featurestore_sqlview()
        self.upload_style()
        self.publish_style()
