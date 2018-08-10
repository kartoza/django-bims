__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '20/06/18'

import math


def update_min_bbox(point, min_bbox):
    """
    For every cluster we are calculating minimum bbox for point in the
    cluster
    This is required in order to have nicer click to zoom map behaviour
    (fitBounds)
    This minimum bbox is used for calculating the clustering of points for
    the next point.

    :param point: point that will be used for creating new minimum bbox
    :type point: tuple

    :param min_bbox: old minimum bbox that will be updated.
    :type min_bbox: tuple

    :return new_min_bbox: new minimum bbox.
    :rtype new_min_bbox: tuple
    """

    new_min_bbox = list(min_bbox)

    if point[0] < min_bbox[0]:
        new_min_bbox[0] = point[0]
    if point[0] > min_bbox[2]:
        new_min_bbox[2] = point[0]
    if point[1] < min_bbox[1]:
        new_min_bbox[1] = point[1]
    if point[1] > min_bbox[3]:
        new_min_bbox[3] = point[1]

    return new_min_bbox


def within_bbox(point, bbox):
    """
    Check if a point (x, y) is within a bbox (minx, miny, maxx, maxy)

    :param point: point that will be checked.
    :type point: tuple

    :param bbox: bbox that will be used for checking point is within bbox.
    :type bbox: tuple

    :return: is point within bbox or not
    :rtype: bool
    """

    if bbox[0] < point[0] < bbox[2] and bbox[1] < point[1] < bbox[3]:
        return True
    else:
        return False


def get_center_of_bbox(bbox):
    """
    Get center of bbox

    :param bbox: bbox.
    :type bbox: tuple

    :return: point of center of bbox
    :rtype: list
    """
    return (((bbox[2] - bbox[0]) / 2) + bbox[0],
            ((bbox[3] - bbox[1]) / 2) + bbox[1])


def overlapping_area(zoom, pix_x, pix_y, lat):
    """
    Calculate an area (lng_deg, lat_deg) in degrees for an icon
    and a zoom
    Since we are using a World Mercator projection deformation is
    uniform in all directions and depends only on latitude

    :param zoom: zoom level of map
    :type zoom: int

    :param pix_x: pixel x of icon
    :type pix_x: int

    :param pix_y: pixel y of icon
    :type pix_y: int
    """
    C = (2 * 6378137.0 * math.pi) / 256.  # one pixel
    C2 = (2 * 6378137.0 * math.pi) / 360.  # one degree

    lat_deformation = (C * math.cos(math.radians(lat)) / 2 ** zoom)

    lat_deg = (lat_deformation * pix_y) / C2
    lng_deg = (lat_deformation * pix_x) / C2

    return (lng_deg, lat_deg)


def geo_serializer(records):
    """
    Return geojson of records with clean dictionary.

    :param records: raw records
    :type records: list

    :return: geojson records
    :rtype: dict
    """
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for record in records:
        if record['count'] == 1:
            geojson['features'].append(
                {
                    "id": record['record']['id'],
                    "geometry": {
                        "type": "Point",
                        "coordinates": record['coordinates']
                    },
                    "type": "Feature",
                    "properties": record['record']
                }
            )
        else:
            geojson['features'].append(
                {
                    "geometry": {
                        "type": "Point",
                        "coordinates": get_center_of_bbox(
                            record['minbbox']
                        )
                    },
                    "type": "Feature",
                    "properties": {
                        'count': record['count']
                    }
                }
            )
    return geojson
