define(['shared', 'backbone', 'underscore', 'jquery', 'jqueryUi', 'jqueryTouch', 'ol', 'views/layer_style'], function (Shared, Backbone, _, $, jqueryUI,jqueryTouch, ol, LayerStyle) {
    return Backbone.View.extend({
        // source of layers
        biodiversitySource: null,
        biodiversityTileLayer: null,
        locationSiteCluster: null,
        locationSiteClusterLayer: null,
        locationSiteClusterSource: null,
        highlightVectorSource: null,
        highlightVector: null,
        highlightPinnedVectorSource: null,
        highlightPinnedVector: null,
        administrativeLayerGroup: null,
        layers: {},
        currentAdministrativeLayer: "",
        administrativeKeyword: "Administrative",
        initialLoadBiodiversityLayersToMap: false,
        administrativeTransparency: 100,
        orders: {},
        administrativeOrder: 0,
        layerSelector: null,
        administrativeLayersName: ["Administrative Provinces", "Administrative Municipals", "Administrative Districts"],
        sleepTimeOut: false,
        initialize: function () {
            this.layerStyle = new LayerStyle();
            Shared.Dispatcher.on('layers:showFeatureInfo', this.showFeatureInfo, this);
            var administrativeVisibility = Shared.StorageUtil.getItemDict('Administrative', 'transparency');
            if (administrativeVisibility !== null) {
                this.administrativeTransparency = administrativeVisibility;
            }
        },
        isBiodiversityLayerLoaded: function () {
            return true;
        },
        isAdministrativeLayerSelected: function () {
            var $checkbox = $('.layer-selector-input[value="Administrative"]');
            if ($checkbox.length === 0) {
                return true
            }
            return $checkbox.is(':checked');
        },
        initLayer: function (layer, layerName, visibleInDefault, category, source) {
            layer.set('added', false);
            var layerType = layerName;
            var layerSource = '';
            var layerCategory = '';
            try {
                var layerOptions = layer.getSource()['i'];
                if (layerOptions) {
                    layerType = layer.getSource()['i']['layers'];
                }
            } catch (e) {
                if (e instanceof TypeError) {
                }
            }
            if (layerName.indexOf(this.administrativeKeyword) >= 0) {
                layerType = layerName;
            }

            var savedLayerVisibility = Shared.StorageUtil.getItemDict(layerType, 'selected');

            if (savedLayerVisibility !== null) {
                visibleInDefault = savedLayerVisibility;
            }

            if (category) {
                layerCategory = category;
            }
            if (source) {
                layerSource = source;
            }

            this.layers[layerType] = {
                'layer': layer,
                'visibleInDefault': visibleInDefault,
                'layerName': layerName,
                'category': layerCategory,
                'source': layerSource
            };
            if (!visibleInDefault) {
                layer.setVisible(false);
            }
        },
        addBiodiveristyLayersToMap: function (map) {
            var self = this;
            // ---------------------------------
            // HIGHLIGHT PINNED LAYER
            // ---------------------------------
            self.highlightPinnedVectorSource = new ol.source.Vector({
            });
            self.highlightPinnedVector = new ol.layer.Vector({
                source: self.highlightPinnedVectorSource,
                style: function (feature) {
                    var geom = feature.getGeometry();
                    return self.layerStyle.getPinnedHighlightStyle(geom.getType());
                }
            });
            map.addLayer(self.highlightPinnedVector);

            // ---------------------------------
            // HIGHLIGHT LAYER
            // ---------------------------------
            self.highlightVectorSource = new ol.source.Vector();
            self.highlightVector = new ol.layer.Vector({
                source: self.highlightVectorSource,
                style: function (feature) {
                    var geom = feature.getGeometry();
                    return self.layerStyle.getHighlightStyle(geom.getType());
                }
            });
            map.addLayer(self.highlightVector);

            // ---------------------------------
            // BIODIVERSITY LAYERS
            // ---------------------------------
            var biodiversityLayersOptions = {
                url: geoserverPublicUrl + 'wms',
                params: {
                    LAYERS: locationSiteGeoserverLayer,
                    FORMAT: 'image/png8',
                    viewparams: 'where:' + defaultWMSSiteParameters
                },
                ratio: 1,
                serverType: 'geoserver'
            };
            self.biodiversitySource = new ol.source.ImageWMS(biodiversityLayersOptions);
            self.biodiversityTileLayer = new ol.layer.Image({
                source: self.biodiversitySource
            });
            self.initLayer(
                self.biodiversityTileLayer,
                'Sites',
                true,
            );

            if (!self.initialLoadBiodiversityLayersToMap) {
                self.initialLoadBiodiversityLayersToMap = true;
            }
        },
        addAdministrativeLayerToMap: function (data) {
            let self = this;
            let currentIndex = 0;
            let _layerName = 'Administrative';
            let _administrativeLayers = [];
            $.each(this.administrativeLayersName, function (idx, layerName) {
                $.each(data, function (index, value) {
                    if (value.name !== layerName) {
                        return
                    }
                    let options = {
                        url: '/bims_proxy/' + encodeURI(value.wms_url),
                        params: {
                            layers: value.wms_layer_name,
                            format: value.wms_format
                        }
                    };
                    let layer = new ol.layer.Tile({
                        source: new ol.source.TileWMS(options)
                    });
                    layer.set('layerName', layerName);
                    layer.setVisible(currentIndex === 0);
                    _administrativeLayers.push(layer);
                    currentIndex += 1;
                });
            });
            self.administrativeLayerGroup = new ol.layer.Group({
                layers: _administrativeLayers
            });

            let _isAdministrativeSelected = Shared.StorageUtil.getItemDict('Administrative', 'selected');
            if (!_isAdministrativeSelected) {
                _isAdministrativeSelected = false;
            }

            self.initLayer(
                self.administrativeLayerGroup,
                _layerName,
               _isAdministrativeSelected
            );
        },
        addLayersToMap: function (map) {
            var self = this;
            this.map = map;

            var biodiversityOrder = Shared.StorageUtil.getItemDict('Sites', 'order');
            if (biodiversityOrder === null) {
                biodiversityOrder = 0;
            }
            self.orders[0] = 'Sites';

            $.ajax({
                type: 'GET',
                url: listNonBiodiversityLayerAPIUrl,
                dataType: 'json',
                success: function (data) {
                    var listNonBioHash = Shared.StorageUtil.getItem('listNonBiodiversity');
                    var hashCurrentList = Shared.StorageUtil.hashItem(JSON.stringify(data));
                    if (!listNonBioHash || listNonBioHash !== hashCurrentList) {
                        Shared.StorageUtil.clear();
                        Shared.StorageUtil.setItem(
                            'listNonBiodiversity',
                            hashCurrentList);
                    }
                    $.each(data, function (index, value) {
                        if (value['name'].indexOf(self.administrativeKeyword) >= 0) {
                            var administrativeOrder = Shared.StorageUtil.getItemDict('Administrative', 'order');
                            if (!administrativeOrder) {
                                self.administrativeOrder = administrativeOrder;
                                return;
                            }
                            if (self.administrativeOrder > 0) {
                                if (parseInt(value['order']) < self.administrativeOrder) {
                                    self.administrativeOrder = value['order'];
                                }
                            } else {
                                self.administrativeOrder = value['order'];
                            }
                            return;
                        }

                        var layerOrder = value['order']+1;
                        self.orders[layerOrder] = value['wms_layer_name'];

                        var defaultVisibility = Shared.StorageUtil.getItemDict(
                            value['wms_layer_name'], 'selected');

                        if (defaultVisibility === null) {
                            defaultVisibility = value['default_visibility'];
                            Shared.StorageUtil.setItemDict(value['wms_layer_name'], 'selected', defaultVisibility);
                        }

                        var options = {
                            url: '/bims_proxy/' + encodeURI(value.wms_url),
                            params: {
                                layers: value.wms_layer_name,
                                format: value.wms_format
                            }
                        };

                        var wmsUrl = value.wms_url;

                        wmsUrl = wmsUrl.replace(/(^\w+:|^)\/\//, '').split('/');
                        if (wmsUrl.length > 0) {
                            wmsUrl = wmsUrl[0];
                        }

                        self.initLayer(
                            new ol.layer.Tile({
                                source: new ol.source.TileWMS(options)
                            }),
                            value.name, false, '', wmsUrl
                        );
                        self.renderLegend(
                            value.wms_layer_name,
                            value.name,
                            options['url'],
                            options['params']['layers'],
                            false
                        );
                    });

                    let administrativeOrder = self.administrativeOrder + 1;
                    self.orders[administrativeOrder] = self.administrativeKeyword;

                    self.addBiodiveristyLayersToMap(map);
                    self.addAdministrativeLayerToMap(data);
                    // Render available layers first because fetching layer from geonode takes time
                    self.renderLayers(true);

                    self.addGeonodeLayersToMap(map);

                },
                error: function (err) {
                    self.addBiodiveristyLayersToMap(map);
                }
            });

        },
        addGeonodeLayersToMap: function (map) {
            // Adding layer from GeoNode, filtering is done by the API
            var default_wms_url = ogcServerDefaultLocation + 'wms';
            var default_wms_format = 'image/png';
            var self = this;

            $.ajax({
                type: 'GET',
                url: '/api/layers',
                dataType: 'json',
                success: function (data) {
                    $.each(data['objects'].reverse(), function (index, value) {
                        if (value['title'].indexOf(self.administrativeKeyword) >= 0) {
                            return;
                        }
                        var options = {
                            url: default_wms_url,
                            params: {
                                layers: value.typename,
                                format: default_wms_format
                            }
                        };

                        var layerName = value.typename;
                        if (!layerName) {
                            return true;
                        }

                        if (layerName.indexOf(self.administrativeKeyword) >= 0 ||
                            layerName === 'null' ||
                            layerName === 'Sites') {
                            return true;
                        }

                        let layerOrder = (parseInt(Object.keys(self.orders)[Object.keys(self.orders).length - 1]) + 1);
                        self.orders[layerOrder] = layerName;

                        var category = '';

                        if (value.hasOwnProperty('category__gn_description')) {
                            category = value['category__gn_description'];
                        }

                        self.initLayer(
                            new ol.layer.Tile({
                                source: new ol.source.TileWMS(options)
                            }),
                            value.title, false, category, 'GeoNode'
                        );

                        self.renderLegend(
                            value.typename,
                            value.title,
                            options['url'],
                            options['params']['layers'],
                            false
                        );
                    });
                    self.renderLayers(false);
                    self.refreshLayerOrders();
                }
            })
        },
        changeLayerAdministrative: function (administrative) {
            var self = this;
            var administrativeVisibility = Shared.StorageUtil.getItemDict('Administrative', 'selected');
            if (!self.isAdministrativeLayerSelected() || !administrativeVisibility || !self.administrativeLayerGroup) {
                return false;
            }
            for (let i = 0; i < self.administrativeLayerGroup.getLayers().getLength(); i++) {
                let _administrativeLayer = self.administrativeLayerGroup.getLayers().item(i);
                let _layerName = _administrativeLayer.get('layerName');
                if (_layerName.toLowerCase().indexOf(administrative) > -1) {
                    self.currentAdministrativeLayer = _layerName;
                    _administrativeLayer.setVisible(true);
                } else {
                    _administrativeLayer.setVisible(false);
                }
            }
            this.changeLayerTransparency(this.administrativeKeyword, this.administrativeTransparency);
        },
        changeLayerVisibility: function (layerName, visible) {
            if (Object.keys(this.layers).length === 0) {
                return false;
            }
            this.layers[layerName]['layer'].setVisible(visible);
        },
        changeLayerTransparency: function (layername, opacity) {
            if (Object.keys(this.layers).length === 0) {
                return false;
            }
            this.layers[layername]['layer'].setOpacity(opacity);
        },
        selectorChanged: function (layerName, selected) {
            Shared.StorageUtil.setItemDict(layerName, 'selected', selected);
            this.changeLayerVisibility(layerName, selected);
            var needToReloadXHR = true;
            this.toggleLegend(layerName, selected, needToReloadXHR);
        },
        toggleLegend: function (layerName, selected, reloadXHR) {
            // show/hide legend
            var $legendElement = this.getLegendElement(layerName);
            if (layerName === 'Sites' && this.isBiodiversityLayerLoaded()) {
                if (reloadXHR) {
                    Shared.Dispatcher.trigger('map:reloadXHR');
                }
                if (selected) {
                    Shared.Dispatcher.trigger('biodiversityLegend:show');
                } else {
                    Shared.Dispatcher.trigger('biodiversityLegend:hide');
                }
            }

            if (selected) {
                if ($legendElement.length > 0) {
                    $legendElement.show();
                    Shared.Dispatcher.trigger('map:showMapLegends');
                }
            } else {
                $legendElement.hide();
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
        renderLegend: function (id, name, url, layer, visibleDefault) {
            var scr = url + '?request=GetLegendGraphic&format=image/png&width=40&height=40&layer=' + layer;
            if (url.indexOf('.qgs') != -1) {
                scr = url + '&service=WMS&request=GetLegendGraphic&format=image/png&transparent=true&width=40&height=40&layer=' + layer;
            }
            var html =
                '<div data-name="' + id + '" class="legend-row"';
            if (!visibleDefault) {
                html += ' style="display: None"'
            }
            html += '>' +
                '<b>' + name + '</b><br>' +
                '<img src="' + scr + '"></div>';
            $('#map-legend').prepend(html);
        },
        renderLayersSelector: function (key, name, visibleInDefault, transparencyDefault, category, source, isFirstTime) {
            if ($('.layer-selector-input[value="' + key + '"]').length > 0) {
                return
            }
            var self = this;
            var mostTop = 'Sites';
            var checked = '';
            if (visibleInDefault) {
                checked += 'checked';
            }
            if (name === mostTop) {
                name = '<b>' + name + '</b>';
            }

            var layerSelectorSearch = Shared.StorageUtil.getItem('layerSelectorSearch');
            var layerDisplayed = 'block';
            if (layerSelectorSearch) {
                if (name.toLowerCase().indexOf(layerSelectorSearch.toLowerCase()) === -1) {
                    layerDisplayed = 'none';
                }
            }

            var tags = '';
            var layerId = name;
            if (!source) {
                    source = '';
            }
            if (!category) {
                    category = '';
            }
            var rowTemplate = _.template($('#layer-selector-row').html());
            let $rowTemplate = $(rowTemplate({
                    id: layerId,
                    name: name,
                    key: key,
                    checked: checked,
                    transparency_value: transparencyDefault,
                    display: layerDisplayed,
                    source: source,
                    category: category,
            }));
            if (isFirstTime) {
                $rowTemplate.prependTo('#layers-selector').find('.layer-selector-tags').append(tags);
            } else {
                $rowTemplate.appendTo('#layers-selector').find('.layer-selector-tags').append(tags);
            }

            var needToReloadXHR = false;
            self.toggleLegend(key, visibleInDefault, needToReloadXHR);
        },
        renderTransparencySlider: function () {
            var self = this;
            var layerDivs = $('#layers-selector').find('.layer-transparency');
            $.each(layerDivs, function (key, layerDiv) {
                $(layerDiv).slider({
                    range: 'max',
                    min: 1,
                    max: 100,
                    value: $(layerDiv).data('value'),
                    slide: function (event, ui) {
                        var $label = $(event.target).closest('li').find('.layer-selector-input');
                        var layername = 'Sites';
                        if ($label.length > 0) {
                            layername = $label.val();
                        }
                        self.changeLayerTransparency(layername, ui.value / 100);
                    },
                    stop: function (event, ui) {
                        var $label = $(event.target).closest('li').find('.layer-selector-input');
                        var layername = 'Sites';
                        if ($label.length > 0) {
                            layername = $label.val();
                        }
                        Shared.StorageUtil.setItemDict(layername, 'transparency', ui.value / 100);
                        if (layername.indexOf(self.administrativeKeyword) >= 0) {
                            self.administrativeTransparency = ui.value / 100;
                        }
                    }
                });
            });
        },
        renderLayers: function (isFirstTime) {
            let self = this;
            let savedOrders = $.extend({}, self.orders);

            // Reverse orders
            let reversedOrders = savedOrders;
            if (isFirstTime) {
                reversedOrders = [];
                $.each(savedOrders, function (key, value) {
                    reversedOrders.unshift(value);
                });
            }

            $.each(reversedOrders, function (index, key) {
                var value = self.layers[key];
                var layerName = '';
                var defaultVisibility = false;
                var category = '';
                var source = '';

                if (typeof value !== 'undefined') {
                    layerName = value['layerName'];
                    defaultVisibility = value['visibleInDefault'];
                    if (value.hasOwnProperty('category')) {
                        category = value['category'];
                    }
                    if (value.hasOwnProperty('source')) {
                        source = value['source'];
                    }
                } else {
                    layerName = key;
                }

                if (typeof layerName === 'undefined') {
                    return true;
                }

                var currentLayerTransparency = 100;

                // Get saved transparency data from storage
                var itemName = key;
                var layerTransparency = Shared.StorageUtil.getItemDict(itemName, 'transparency');
                if (layerTransparency !== null) {
                    currentLayerTransparency = layerTransparency * 100;
                    self.changeLayerTransparency(itemName, layerTransparency);
                } else {
                    currentLayerTransparency = 100;
                }

                if (layerName.indexOf(self.administrativeKeyword) >= 0) {
                    var administrativeVisibility = Shared.StorageUtil.getItem('Administrative');
                    if (administrativeVisibility === null) {
                        administrativeVisibility = true;
                    } else {
                        if (administrativeVisibility.hasOwnProperty('selected')) {
                            administrativeVisibility = administrativeVisibility['selected'];
                        }
                    }
                    defaultVisibility = administrativeVisibility;
                    source = 'Base';
                }

                self.renderLayersSelector(key, layerName, defaultVisibility, currentLayerTransparency, category, source, isFirstTime);
            });

            // RENDER LAYERS
            $.each(self.layers, function (key, value) {
                let _layer = value['layer'];
                if (!_layer.get('added')) {
                    _layer.set('added', true);
                    self.map.addLayer(_layer);
                }
            });
            self.renderTransparencySlider();

            $('.layer-selector-input').change(function (e) {
                self.selectorChanged($(e.target).val(), $(e.target).is(':checked'))
            });


            if (isFirstTime) {
                self.initializeLayerSelector();
            }
            $('.layer-source').unbind('click');
            $('.layer-source').click(function (e) {
                self.showLayerSource(e.target.attributes["value"].value);
                return false;
            });
        },
        showFeatureInfo: function (coordinate) {
            if (Shared.GetFeatureRequested) {
                Shared.GetFeatureRequested = false;
                Shared.Dispatcher.trigger('map:hidePopup');
                if (Shared.GetFeatureXHRRequest.length > 0) {
                    $.each(Shared.GetFeatureXHRRequest, function (index, request) {
                        request.abort();
                    });
                    Shared.GetFeatureXHRRequest = [];
                }
                return;
            }
            var that = this;
            var lastCoordinate = coordinate;
            var view = this.map.getView();
            var featuresInfo = {};
            Shared.GetFeatureRequested = true;
            Shared.Dispatcher.trigger('map:showPopup', coordinate,
                    '<div class="info-popup popup-loading"> Fetching... </div>');
            $.each(this.layers, function (layer_key, layer) {
                if (coordinate !== lastCoordinate) {
                    return;
                }
                if (layer['layer'].getVisible()) {
                    try {
                        var queryLayer = layer['layer'].getSource().getParams()['layers'];
                        var layerSource = layer['layer'].getSource().getGetFeatureInfoUrl(
                            coordinate,
                            view.getResolution(),
                            view.getProjection(),
                            {'INFO_FORMAT': 'text/plain'}
                        );
                        layerSource += '&QUERY_LAYERS=' + queryLayer;

                        Shared.GetFeatureXHRRequest.push($.ajax({
                            type: 'POST',
                            url: '/get_feature/',
                            data: {
                                'layerSource': layerSource
                            },
                            success: function (data) {
                                // process properties
                                if (coordinate !== lastCoordinate || !data) {
                                    return;
                                }
                                var linesData = data.split("\n");
                                var properties = {};

                                //reformat plain text to be dictionary
                                // because qgis can't support info format json
                                $.each(linesData, function (index, string) {
                                    var couple = string.split(' = ');
                                    if (couple.length !== 2) {
                                        return true;
                                    } else {
                                        if (couple[0] === 'geom') {
                                            return true;
                                        }
                                        properties[couple[0]] = couple[1];
                                    }
                                });
                                if ($.isEmptyObject(properties)) {
                                    return;
                                }
                                featuresInfo[layer_key] = {
                                    'layerName': layer['layerName'],
                                    'properties': properties
                                };
                            },
                        }));
                    } catch (err) {

                    }
                }
            });
            Promise.all(Shared.GetFeatureXHRRequest).then(() => {
                that.renderFeaturesInfo(featuresInfo, coordinate);
                Shared.GetFeatureXHRRequest = [];
            }).catch((err) => {
                if (Shared.GetFeatureXHRRequest.length > 0) {
                    Shared.Dispatcher.trigger('map:showPopup', coordinate,
                        '<div class="info-popup popup-error">Failed to fetch feature info</div>');
                    Shared.GetFeatureXHRRequest = [];
                }
            });
        },
        renderFeaturesInfo: function (featuresInfo, coordinate) {
            var that = this;
            let tabs = '<ul class="nav nav-tabs">';
            let content = '';
            $.each(featuresInfo, function (key_feature, feature) {
                var layerName = feature['layerName'];
                if (layerName.indexOf(that.administrativeKeyword) >= 0) {
                    layerName = that.administrativeKeyword;
                    key_feature = 'administrative';
                }
                tabs += '<li ' +
                    'role="presentation" class="info-wrapper-tab"  ' +
                    'title="' + layerName + '" ' +
                    'data-tab="info-' + key_feature + '">' +
                    layerName + '</li>';
                content += '<div class="info-wrapper" data-tab="info-' + key_feature + '">';
                content += '<table>';
                $.each(feature['properties'], function (key, property) {
                    content += '<tr>';
                    content += '<td>' + key + '</td>';
                    content += '<td>' + property + '</td>';
                    content += '</tr>'
                });
                content += '</table>';
                content += '</div>';
            });
            tabs += '</ul>';
            Shared.Dispatcher.trigger('map:showPopup', coordinate,
                '<div class="info-popup">' + tabs + content + '</div>');
            let infoWrapperTab = $('.info-wrapper-tab');

            infoWrapperTab.click(function () {
                infoWrapperTab.removeClass('active');
                $(this).addClass('active');

                $('.info-wrapper').hide();
                $('.info-wrapper[data-tab="' + $(this).data('tab') + '"]').show();
            });
            if ($('.nav-tabs').innerHeight() > $(infoWrapperTab[0]).innerHeight()) {
                let width = $('.info-popup').width() / infoWrapperTab.length;
                infoWrapperTab.innerWidth(width);
            }
            infoWrapperTab[0].click();
        },
        showLayerSource: function (layerKey) {
                if (Object.keys(this.layers).length === 0) {
                    return false;
                }
                else if (layerKey !== this.administrativeKeyword) {
                    this.getLayerAbstract(layerKey);
                }
            },
        getLayerAbstract: function(layerKey) {
            if (layerKey.indexOf(":") > 0) {
                layerProvider = layerKey.split(":")[0];
                layerName = layerKey.split(":")[1];
            }
            else {
                layerProvider = layerKey;
                layerName = layerKey;
            }
            let url_provider = layerProvider;
            let url_key = layerName;
            var abstract_result = "";
            $.ajax({
                type: 'GET',
                url: `http://maps.kartoza.com/geoserver/${url_provider}/${url_key}/wms?request=getCapabilities`,
                dataType: `xml`,
                success: function(response){
                    var xml_response, parser, xmlDoc;
                    xml_response = response['documentElement']['innerHTML'];
                    xml_response = xml_response.replace(/[\r\n]*/g, "");
                    xml_response = xml_response.replace("\\n", "");
                    xml_response = '<document>' + xml_response.replace(" ", "") + '</document>';

                    parser = new DOMParser();
                    xmlDoc = parser.parseFromString(xml_response, 'text/xml');
                    try{
                        abstract_result = xmlDoc.getElementsByTagName("Abstract")[2].childNodes[0].nodeValue;
                    }
                    catch (e) {
                        abstract_result = "Abstract information unavailable.";
                    }
                },
                error (err) {
                    abstract_result = "Abstract information unavailable.";
                    return false;
                },

                complete () {
                    layerSourceContainer = $('div.layer-source-info[value="'+ layerKey + '"]');
                    if (layerSourceContainer.html() == "")
                    {

                        layerSourceContainer.html(`
                            <div class="layer-abstract">
                                ` + abstract_result + `
                            </div>`);
                        layerSourceContainer.toggle();
                    }
                    layerSourceContainer.slideToggle(400);
                },
            })

        },

        initializeLayerSelector: function () {
            let self = this;
            this.layerSelector = $('#layers-selector');
            this.layerSelector.sortable();
            this.layerSelector.on('sortupdate', function () {
                let $layerSelectorInput = $('.layer-selector-input');
                $($layerSelectorInput.get().reverse()).each(function (index, value) {
                    let layerName = $(value).val();
                    self.moveLayerToTop(self.layers[layerName]['layer']);
                    self.moveLegendToTop(layerName);
                });
                self.moveLayerToTop(self.highlightPinnedVector);
                self.moveLayerToTop(self.highlightVector);

                // Update saved order
                $($layerSelectorInput.get()).each(function (index, value) {
                    let layerName = $(value).val();
                    Shared.StorageUtil.setItemDict(layerName, 'order', parseInt(index));
                });
            });
        },
        changeLayerOder: function (layerName, order) {
            let $layerElm = $('.layer-selector-input[value="' + layerName + '"]').parent().parent();
            let $layerSelectorList = $('#layers-selector li');
            if (order > $layerSelectorList.length - 1) {
                order = $layerSelectorList.length - 1;
            }
            if (order <= 0) {
                $layerElm.insertBefore($layerSelectorList.get(0));
            } else {
                $layerElm.insertAfter($layerSelectorList.get(order - 1));
            }
        },
        refreshLayerOrders: function () {
            let self = this;
            let $layerSelectorInput = $('.layer-selector-input');
            $($layerSelectorInput.get()).each(function (index, value) {
                let layerName = $(value).val();
                let order = Shared.StorageUtil.getItemDict(layerName, 'order');
                if (order != null) {
                    self.changeLayerOder(layerName, order);
                }
            });
            self.layerSelector.trigger('sortupdate');
        }
    })
});
