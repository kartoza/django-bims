define(['backbone', 'underscore', 'jquery'], function (Backbone, _, $) {
    return Backbone.View.extend({
        maxCount: 500,
        maxRadius: 30,
        styles: {
            'Point': new ol.style.Style({
                image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                    anchor: [0.5, 46],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 0.75,
                    src: '/static/img/map-marker.png'
                })),
                text: new ol.style.Text({
                    scale: 1,
                    fill: new ol.style.Fill({
                        color: '#000000'
                    })
                })
            }),
            'LineString': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'green',
                    width: 1
                })
            }),
            'MultiPolygon': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'yellow',
                    width: 1
                }),
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 0, 0.1)'
                })
            }),
            'Polygon': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'blue',
                    lineDash: [4],
                    width: 3
                }),
                fill: new ol.style.Fill({
                    color: 'rgba(0, 0, 255, 0.1)'
                })
            })
        },
        administrativeBoundaryStyle: function (feature) {
            return new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'yellow',
                    width: 1
                }),
                text: new ol.style.Text({
                    scale: 1,
                    fill: new ol.style.Fill({
                        color: '#000000'
                    }),
                    text: feature.getProperties()['name']
                })
            })
        },
        getBiodiversityStyle: function (feature) {
            var type = feature.getGeometry().getType();
            if (type !== 'Point') {
                return this.styles[type];
            } else {
                return this.getClusterStyle(feature);
            }
        },
        isIndividialCluster: function (feature, count) {
            if (!count) {
                count = feature.getProperties()['count'];
            }
            var boundary_type = feature.getProperties()['boundary_type'];
            return (!boundary_type && (!count || count === 1))
        },
        getClusterStyle: function (feature, count) {
            if (!count) {
                count = feature.getProperties()['count'];
            }
            var radius = 10;
            var image = null;
            if (this.isIndividialCluster(feature, count)) {
                radius = 8;
                image = new ol.style.Circle({
                    radius: radius,
                    fill: new ol.style.Fill({
                        color: '#18A090'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#fff',
                        width: 2
                    })
                });
            } else {
                var currentCount = count;
                var clusterColor = '';
                if (currentCount > this.maxCount) {
                    currentCount = this.maxCount;
                }
                radius += (currentCount / this.maxCount) * this.maxRadius;

                if (count >= 500) {
                    clusterColor = '#9a791d';
                } else if (count >= 100) {
                    clusterColor = '#bd9524';
                } else if (count >= 10) {
                    clusterColor = '#d0b547';
                } else {
                    clusterColor = '#e8e251';
                }

                image = new ol.style.Circle({
                    radius: radius,
                    fill: new ol.style.Fill({
                        color: clusterColor
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#fff',
                        width: 2
                    })
                });
            }
            var textStyle = {
                scale: 1.3,
                fill: new ol.style.Fill({
                    color: '#fff'
                }),
                'font': 'bold 11px "Roboto Condensed"'
            };
            if (count > this.maxCount) {
                textStyle['text'] = '>' + this.maxCount;
            } else if (count > 100) {
                textStyle['text'] = '>100';
            }
            return new ol.style.Style({
                image: image,
                text: new ol.style.Text(textStyle)
            });
        },
        getHighlightStyle: function (geometryType) {
            var style;
            if (geometryType != 'Point') {
                style = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: [255, 0, 0, 0.8],
                        width: 2
                    }),
                    fill: new ol.style.Fill({
                        color: [255, 0, 0, 0.8]
                    })
                })
            } else {
                style = new ol.style.Style({
                    image: new ol.style.Icon(({
                        anchor: [0.5, 46],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        opacity: 0.75,
                        src: '/static/img/map-marker-highlight.png'
                    })),
                    text: new ol.style.Text({
                        scale: 1,
                        fill: new ol.style.Fill({
                            color: '#000000'
                        })
                    })
                })
            }
            return style;
        },
        getPinnedHighlightStyle: function (geometryType) {
            var style;
            if (geometryType != 'Point') {
                style = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: [0, 255, 0, 1],
                        width: 2
                    }),
                    fill: new ol.style.Fill({
                        color: [0, 255, 0, 0.2]
                    })
                })
            } else {
                style = new ol.style.Style({
                    image: new ol.style.Icon(({
                        anchor: [0.5, 46],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        opacity: 0.75,
                        src: '/static/img/map-marker-highlight.png'
                    })),
                    text: new ol.style.Text({
                        scale: 1,
                        fill: new ol.style.Fill({
                            color: '#000000'
                        })
                    })
                })
            }
            return style;
        }
    })
});
