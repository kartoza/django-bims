define(['shared', 'backbone', 'underscore', 'jquery', 'ol', 'views/layer_style'], function (Shared, Backbone, _, $, ol, LayerStyle) {
    return Backbone.View.extend({
        // source of layers
        biodiversitySource: null,
        highlightVectorSource: null,
        highlightVector: null,
        layers: {},
        currentAdministrativeLayer: "",
        administrativeKeyword: "Administrative",
        administrativeLayersName: ["Administrative Provinces", "Administrative Municipals", "Administrative Districts"],
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
        addBiodiveristyLayersToMap: function (map) {
            var self = this;

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
        addLayersToMap: function (map) {
            var self = this;
            this.map = map;

            $.ajax({
                type: 'GET',
                url: listNonBiodiversityLayerAPIUrl,
                dataType: 'json',
                success: function (data) {
                    $.each(data.reverse(), function (index, value) {
                        if (value['name'].indexOf(self.administrativeKeyword) >= 0) {
                            return;
                        }
                        var options = {
                            url: value.wms_url,
                            params: {
                                layers: value.wms_layer_name,
                                format: value.wms_format
                            }
                        };
                        self.initLayer(
                            new ol.layer.Tile({
                                source: new ol.source.TileWMS(options)
                            }),
                            value.name, false
                        );
                        self.renderLegend(
                            value.name,
                            options['url'],
                            options['params']['layers'],
                            false
                        );
                    });

                    // add Administrative boundary
                    self.renderAdministrativeLayer(data);
                    self.addBiodiveristyLayersToMap(map);
                },
                error: function (err) {
                    self.addBiodiveristyLayersToMap(map);
                }
            });
        },
        isBiodiversityLayerShow: function () {
            var $checkbox = $('.layer-selector-input[value="Biodiversity"]');
            if ($checkbox.length == 0) {
                return true
            }
            return $checkbox.is(':checked');
        },
        changeLayerAdministrative: function (administrative) {
            var self = this;
            switch (administrative) {
                case 'province':
                    self.currentAdministrativeLayer = self.administrativeLayersName[0];
                    break;
                case 'district':
                    self.currentAdministrativeLayer = self.administrativeLayersName[1];
                    break;
                case 'municipal':
                    self.currentAdministrativeLayer = self.administrativeLayersName[2];
                    break;
            }
            $.each(self.administrativeLayersName, function (idx, layerName) {
                if (self.layers[layerName]) {
                    self.layers[layerName]['layer'].setVisible(false);
                }
            });
            this.changeLayerVisibility(this.administrativeKeyword, true);
        },
        changeLayerVisibility: function (layerName, visible) {
            if (layerName !== this.administrativeKeyword) {
                this.layers[layerName]['layer'].setVisible(visible);
            } else {
                this.layers[this.currentAdministrativeLayer]['layer'].setVisible(visible);
            }
        },
        selectorChanged: function (layerName, selected) {
            if (layerName === "Biodiversity") {
                Shared.Dispatcher.trigger('map:reloadXHR');
            }
            this.changeLayerVisibility(layerName, selected);

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
        moveLegendToTop: function (layerName) {
            this.getLegendElement(layerName).detach().prependTo('#map-legend');
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
        renderAdministrativeLayer: function (data) {
            var self = this;
            var currentIndex = 0;
            $.each(this.administrativeLayersName, function (idx, layerName) {
                $.each(data, function (index, value) {
                    if (value.name !== layerName) {
                        return
                    }
                    var options = {
                        url: value.wms_url,
                        params: {
                            layers: value.wms_layer_name,
                            format: value.wms_format
                        }
                    };
                    var initVisible = false;
                    if (currentIndex === 0) {
                        initVisible = true;
                        self.currentAdministrativeLayer = layerName;
                    }
                    self.initLayer(
                        new ol.layer.Tile({
                            source: new ol.source.TileWMS(options)
                        }),
                        value.name, initVisible
                    );
                    currentIndex += 1;
                    return false;
                });
            });

        },
        renderLayersSelector: function (key, visibleInDefault) {
            if ($('.layer-selector-input[value="' + key + '"]').length > 0) {
                return
            }
            var mostTop = 'Biodiversity';
            var selector = '<li class="ui-state-default"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><input type="checkbox" value="' + key + '" class="layer-selector-input" ';
            if (visibleInDefault) {
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
        },
        renderLayers: function () {
            var self = this;
            $(document).ready(function () {
                var keys = Object.keys(self.layers);
                keys.reverse();
                $.each(keys, function (index, key) {
                    var value = self.layers[key];
                    if (key.indexOf(self.administrativeKeyword) >= 0) {
                        self.renderLayersSelector('Administrative', true);
                    } else {
                        self.renderLayersSelector(key, value['visibleInDefault']);
                    }
                });
                $('.layer-selector-input').change(function (e) {
                    self.selectorChanged($(e.target).val(), $(e.target).is(':checked'))
                });
                $('#layers-selector').sortable({
                    update: function () {
                        $($(".layer-selector-input").get().reverse()).each(function (index, value) {
                            var layerName = $(value).val();
                            if (layerName !== self.administrativeKeyword) {
                                self.moveLayerToTop(
                                    self.layers[layerName]['layer']);
                                self.moveLegendToTop(layerName);
                            } else {
                                $.each(self.administrativeLayersName, function (idx, layerName) {
                                    if (self.layers[layerName]) {
                                        self.moveLayerToTop(
                                            self.layers[layerName]['layer']);
                                        self.moveLegendToTop(layerName);
                                    }
                                });
                            }
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
