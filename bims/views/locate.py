# coding=utf-8
"""Locate utilities view."""

import requests
from xml.dom import minidom
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from django.http import JsonResponse

from django.http import QueryDict


def get_farm(farm_id):
    """Retrieve farm geometry and properties from GeoServer.


    :param farm_id: The farm farm ID.
    :type farm_id: basestring

    :returns: Dictionary that contains envelope, farm id, etc
    :rtype: dict
    """
    url = settings.FARM_GEOSERVER_URL

    parameters = {
        'SERVICE': 'WFS',
        'VERSION': '2.0.0',
        'REQUEST': 'GETFEATURE',
        'TYPENAME': settings.FARM_WORKSPACE + ':' + settings.FARM_LAYER_NAME,
        'PROPERTYNAME': settings.FARM_ID_COLUMN,
        'CQL_FILTER': "%s = '%s'" % (
            settings.FARM_ID_COLUMN, farm_id)
    }

    query_dict = QueryDict('', mutable=True)
    query_dict.update(parameters)

    if '?' in url:
        url = url + '&' + query_dict.urlencode()
    else:
        url = url + '?' + query_dict.urlencode()

    request = requests.get(url)
    content = request.content

    return parse_farm(content)


def filter_farm_ids(farm_id_pattern):
    """Retrieve Farm IDs with filtering by id pattern.

    :param farm_id_pattern: A pattern to farm ID.
    :type farm_id_pattern: basestring

    :returns: A list of farm ID.
    :rtype: list
    """
    url = settings.FARM_GEOSERVER_URL

    # Adding % in front and end of pattern
    if not farm_id_pattern.startswith('%'):
        farm_id_pattern = '%' + farm_id_pattern

    if not farm_id_pattern.endswith('%'):
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

    return parse_farm_ids(content)


def parse_farm_ids(xml_document):
    """Parse locate xml document from requesting GeoServer.

    :param xml_document: XML document from GeoServer returns.
    :type xml_document: basestring

    :returns: A list of farm ID.
    :rtype: list
    """
    xmldoc = minidom.parseString(xml_document)
    farm_ids = []

    try:
        wfs_xml_features = xmldoc.getElementsByTagName('wfs:member')
        for wfs_xml_feature in wfs_xml_features:
            id_tag = settings.FARM_WORKSPACE + ':' + settings.FARM_ID_COLUMN
            farm_id_xml = wfs_xml_feature.getElementsByTagName(id_tag)[0]
            farm_id = farm_id_xml.childNodes[0].nodeValue
            farm_ids.append(farm_id)
        return farm_ids
    except IndexError:
        return farm_ids


def parse_farm(xml_document):
    """Parse locate xml document from requesting GeoServer.

    :param xml_document: XML document from GeoServer returns.
    :type xml_document: basestring

    :returns: Dictionary that contains envelope, farm id, etc
    :rtype: dict
    """
    xmldoc = minidom.parseString(xml_document)
    feature = {}

    try:
        wfs_xml_feature = xmldoc.getElementsByTagName('wfs:member')[0]

        id_tag = settings.FARM_WORKSPACE + ':' + settings.FARM_ID_COLUMN
        farm_id_xml = wfs_xml_feature.getElementsByTagName(id_tag)[0]
        feature['farm_id'] = farm_id_xml.childNodes[0].nodeValue

        bounded_gml = wfs_xml_feature.getElementsByTagName('gml:boundedBy')[0]
        bounded_gml_dom = bounded_gml.childNodes[0]
        envelope_extent = GEOSGeometry.from_gml(bounded_gml_dom.toxml()).extent
        feature['envelope_extent'] = envelope_extent

        return feature

    except IndexError:
        return feature


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


def filter_farm_ids_view(request, farm_id_pattern):
    """View to filter farm ID. Return JSON."""

    farm_ids = filter_farm_ids(farm_id_pattern)

    data = {
        'farm_ids': sorted(farm_ids)
    }

    return JsonResponse(data)


def get_farm_view(request, farm_id):
    """View to get a farm from an ID. Return JSON."""

    farm = get_farm(farm_id)

    return JsonResponse(farm)
