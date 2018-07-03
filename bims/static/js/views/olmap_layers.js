define(['backbone', 'underscore', 'jquery', 'ol', 'views/layer_style'], function (Backbone, _, $, ol, LayerStyle) {
    return Backbone.View.extend({
        nonBiodiversityLayersInitiation: {
            '2012 Vegetation Map of South Africa, Lesotho and Swaziland': new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: 'http://lbimsgis.kartoza.com/geoserver/wms',
                    params: {
                        'layers': 'geonode:vegetation_map_2012',
                        'format': 'image/png'
                    }
                })
            }),
            'Biomes of South Africa': new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: 'http://lbimsgis.kartoza.com/geoserver/wms',
                    params: {
                        'layers': 'geonode:biomes_of_south_africa_dea_csir',
                        'format': 'image/png'
                    }
                })
            }),
            'South Africa Dams Polygon': new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: 'http://lbimsgis.kartoza.com/geoserver/wms',
                    params: {
                        'layers': 'geonode:dams500g',
                        'format': 'image/png'
                    }
                })
            }),
            'South Africa Towns': new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: 'http://lbimsgis.kartoza.com/geoserver/wms',
                    params: {
                        'layers': 'geonode:sa_towns',
                        'format': 'image/png'
                    }
                })
            }),
            'World Heritage Sites': new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: 'http://lbimsgis.kartoza.com/geoserver/wms',
                    params: {
                        'layers': 'geonode:world_heritage_sites',
                        'format': 'image/png'
                    }
                })
            })
        },
        // source of layers
        administrativeBoundarySource: null,
        biodiversitySource: null,
        highlightVectorSource: null,
        layers: {},
        initialize: function () {
            this.layerStyle = new LayerStyle();
        },
        initLayer: function (layer, layerName, visibleInDefault) {
            this.layers[layerName] = {
                'layer': layer,
                'visibleInDefault': visibleInDefault
            };
            if (!visibleInDefault) {
                layer.setVisible(false);
            }
        },
        addLayersToMap: function (map) {
            var self = this;
            this.map = map;

            // RENDER NON BIODIVERSITY LAYERS
            var keys = Object.keys(self.nonBiodiversityLayersInitiation);
            keys.reverse();
            $.each(keys, function (index, key) {
                self.initLayer(self.nonBiodiversityLayersInitiation[key], key, false)
            });
            // ---------------------------------
            // ADMINISTRATIVE BOUNDARY LAYER
            // ---------------------------------
            self.administrativeBoundarySource = new ol.source.Vector({});
            self.initLayer(new ol.layer.Vector({
                source: self.administrativeBoundarySource,
                style: function (feature) {
                    return self.layerStyle.administrativeBoundaryStyle(feature);
                }
            }), 'Administrative', true);

            // ---------------------------------
            // BIODIVERSITY LAYERS
            // ---------------------------------
            self.biodiversitySource = new ol.source.Vector({});
            self.initLayer(new ol.layer.Vector({
                source: self.biodiversitySource,
                style: function (feature) {
                    return self.layerStyle.getBiodiversityStyle(feature);
                }
            }), 'Biodiversity', true);


            // RENDER LAYERS
            $.each(self.layers, function (key, value) {
                console.log(key);
                map.addLayer(value['layer']);
            });

            // ---------------------------------
            // HIGHLIGHT LAYER
            // ---------------------------------
            self.highlightVectorSource = new ol.source.Vector({});
            map.addLayer(new ol.layer.Vector({
                source: self.highlightVectorSource,
                style: function (feature) {
                    var geom = feature.getGeometry();
                    return self.layerStyle.getHighlightStyle(geom.getType());
                }
            }));
            this.renderLayers();
        },
        selectorChanged: function (layerName, selected) {
            this.layers[layerName]['layer'].setVisible(selected)
        },
        ol3_checkLayer: function (layer) {
            var res = false;
            for (var i = 0; i < this.map.getLayers().getLength(); i++) {
                //check if layer exists
                if (this.map.getLayers().getArray()[i] === layer) {
                    //if exists, return true
                    res = true;
                }
            }
            return res;
        },
        moveLayerToTop: function (layer) {
            if (layer) {
                if (this.ol3_checkLayer(layer)) {
                    this.map.removeLayer(layer);
                    this.map.getLayers().insertAt(this.map.getLayers().getLength(), layer);
                }
            }
        },
        renderLayers: function () {
            var self = this;
            $(document).ready(function () {
                var mostTop = 'Biodiversity';
                var keys = Object.keys(self.layers);
                keys.reverse();
                $.each(keys, function (index, key) {
                    var value = self.layers[key];
                    var selector = '<li class="ui-state-default"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><input type="checkbox" value="' + key + '" class="layer-selector-input" ';
                    if (value['visibleInDefault']) {
                        selector += 'checked';
                    }
                    selector += '>';
                    if (key === mostTop) {
                        selector += '<b>' + key + '</b>';
                    } else {
                        selector += key;
                    }
                    selector += '</li>';
                    $('#layers-selector').append(selector);
                });
                $('.layer-selector-input').change(function (e) {
                    self.selectorChanged($(e.target).val(), $(e.target).is(':checked'))
                });
                $('#layers-selector').sortable({
                    update: function () {
                        $($(".layer-selector-input").get().reverse()).each(function (index, value) {
                            self.moveLayerToTop(
                                self.layers[$(value).val()]['layer']);
                        });
                    }
                });
            });
        }
    })
});
