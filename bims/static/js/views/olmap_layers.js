define(['shared', 'backbone', 'underscore', 'jquery', 'ol', 'views/layer_style'], function (Shared, Backbone, _, $, ol, LayerStyle) {
    return Backbone.View.extend({
        nonBiodiversityLayersUrl: 'http://lbimsgis.kartoza.com/geoserver/wms',
        nonBiodiversityLayersInitiationSource: {
            '2012 Vegetation Map of South Africa, Lesotho and Swaziland': {
                params: {
                    'layers': 'geonode:vegetation_map_2012',
                    'format': 'image/png',
                    'legend-width': 40,
                    'legend-height': 40,
                }
            },
            'Biomes of South Africa': {
                params: {
                    'layers': 'geonode:biomes_of_south_africa_dea_csir',
                    'format': 'image/png',
                    'legend-width': 40,
                    'legend-height': 40,
                }
            },
            'South Africa Dams Polygon': {
                params: {
                    'layers': 'geonode:dams500g',
                    'format': 'image/png'
                }
            },
            'South Africa Towns': {
                params: {
                    'layers': 'geonode:sa_towns',
                    'format': 'image/png'
                }
            },
            'World Heritage Sites': {
                params: {
                    'layers': 'geonode:world_heritage_sites',
                    'format': 'image/png'
                }
            }
        },
        // source of layers
        administrativeBoundarySource: null,
        biodiversitySource: null,
        highlightVectorSource: null,
        highlightVector: null,
        layers: {},
        initialize: function () {
            this.layerStyle = new LayerStyle();
        },
        isBiodiversityLayerShow: function () {
            var $checkbox = $('.layer-selector-input[value="Biodiversity"]');
            return $checkbox.is(':checked');
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
            var keys = Object.keys(self.nonBiodiversityLayersInitiationSource);
            keys.reverse();
            $.each(keys, function (index, key) {
                self.nonBiodiversityLayersInitiationSource[key]['url'] = self.nonBiodiversityLayersUrl;
                self.initLayer(
                    new ol.layer.Tile({
                        source: new ol.source.TileWMS(
                            self.nonBiodiversityLayersInitiationSource[key])
                    }),
                    key, false
                );
                self.renderLegend(
                    key,
                    self.nonBiodiversityLayersInitiationSource[key]['url'],
                    self.nonBiodiversityLayersInitiationSource[key]['params']['layers'],
                    false
                );
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
                map.addLayer(value['layer']);
            });

            // ---------------------------------
            // HIGHLIGHT LAYER
            // ---------------------------------
            self.highlightVectorSource = new ol.source.Vector({});
            self.highlightVector = new ol.layer.Vector({
                source: self.highlightVectorSource,
                style: function (feature) {
                    var geom = feature.getGeometry();
                    return self.layerStyle.getHighlightStyle(geom.getType());
                }
            });
            map.addLayer(self.highlightVector);
            this.renderLayers();
        },
        selectorChanged: function (layerName, selected) {
            if (layerName == "Biodiversity") {
                Shared.Dispatcher.trigger('map:reloadXHR');
            }
            this.layers[layerName]['layer'].setVisible(selected);

            // show/hide legend
            if (selected) {
                this.getLegendElement(layerName).show();
            } else {
                this.getLegendElement(layerName).hide();
            }
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
                } else {
                    console.log('not found')
                }
            }
        },
        getLegendElement: function (layerName) {
            return $(".control-drop-shadow").find(
                "[data-name='" + layerName + "']");
        },
        renderLegend: function (id, url, layer, visibleDefault) {
            var scr = url + '?request=GetLegendGraphic&format=image/png&width=40&height=40&layer=' + layer;
            var html =
                '<div data-name="' + id + '" class="legend-row"';
            if (!visibleDefault) {
                html += ' style="display: None"'
            }
            html += '>' +
                '<b>' + id + '</b><br>' +
                '<img src="' + scr + '"></div>';
            $('#map-legend').prepend(html);
        },
        moveLegendToTop: function (layerName) {
            this.getLegendElement(layerName).detach().prependTo('#map-legend');
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
                            self.moveLegendToTop($(value).val());
                        });
                        self.moveLayerToTop(self.highlightVector);
                    }
                });
                $('#map-legend-wrapper').click(function () {
                    if ($(this).hasClass('hide-legend')) {
                        $(this).removeClass('hide-legend');
                        $(this).addClass('show-legend');
                    } else {
                        $(this).addClass('hide-legend');
                        $(this).removeClass('show-legend');
                    }
                });
            });
        }
    })
});
