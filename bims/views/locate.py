# coding=utf-8
"""Locate utilities view."""

import requests
from xml.dom import minidom
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from django.http import JsonResponse

from django.http import QueryDict


def get_farm_ids(farm_id_pattern):
    """Retrieve Farm IDs from a farm id pattern.

    :param farm_id_pattern: A pattern to farm ID.
    :type farm_id_pattern: basestring

    :returns: A dictionary of farm ID as the key and its envelope as the value.
    :rtype: dict
    """
    url = settings.FARM_GEOSERVER_URL

    # Adding % in the end of pattern
    if '%' not in farm_id_pattern:
        farm_id_pattern = farm_id_pattern + '%'

    parameters = {
        'SERVICE': 'WFS',
        'VERSION': '2.0.0',
        'REQUEST': 'GETFEATURE',
        'TYPENAME': settings.FARM_WORKSPACE + ':' + settings.FARM_LAYER_NAME,
        'PROPERTYNAME': settings.FARM_ID_COLUMN,
        'CQL_FILTER': "%s LIKE '%s'" % (
            settings.FARM_ID_COLUMN, farm_id_pattern)
    }

    query_dict = QueryDict('', mutable=True)
    query_dict.update(parameters)

    if '?' in url:
        url = url + '&' + query_dict.urlencode()
    else:
        url = url + '?' + query_dict.urlencode()

    request = requests.get(url)
    content = request.content

    return parse_locate_return(content)


# TODO(IS): Separate into two method (filter and get)
def parse_locate_return(xml_document, with_envelope=False):
    """Parse locate xml document from requesting GeoServer.

    :param xml_document: XML document from GeoServer returns.
    :type xml_document: basestring

    :returns: A dictionary of farm ID as the key and its envelope as the value.
    :rtype: dict
    """
    xmldoc = minidom.parseString(xml_document)
    features = {}

    try:
        wfs_xml_features = xmldoc.getElementsByTagName('wfs:member')
        for wfs_xml_feature in wfs_xml_features:
            id_tag = settings.FARM_WORKSPACE + ':' + settings.FARM_ID_COLUMN
            farm_id_xml = wfs_xml_feature.getElementsByTagName(id_tag)[0]
            farm_id = farm_id_xml.childNodes[0].nodeValue
            if with_envelope:
                bounded_gml = wfs_xml_feature.getElementsByTagName(
                    'gml:boundedBy')[0]
                bounded_gml_dom = bounded_gml.childNodes[0]
                envelope = GEOSGeometry.from_gml(
                    bounded_gml_dom.toxml()).extent
            else:
                envelope = None
            features[farm_id] = envelope
        return features
    except IndexError:
        return features


def filter_farm_ids(request, farm_id_pattern):
    """View to filter farm ID. Return JSON."""

    farms = get_farm_ids(farm_id_pattern)

    return JsonResponse(farms)
