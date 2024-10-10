define(['shared', 'backbone', 'underscore', 'jquery', 'jqueryUi', 'jqueryTouch', 'views/layer_style'], function (Shared, Backbone, _, $, jqueryUI, jqueryTouch, LayerStyle) {
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
        currentWetlandRequestId: null,
        legends: {},
        wetlandLayer: 'kartoza:nwm6_beta_v3_20230714',
        administrativeLayersName: ["Administrative Provinces", "Administrative Municipals", "Administrative Districts"],
        initialize: function () {
            this.layerStyle = new LayerStyle();
            Shared.Dispatcher.on('layers:showFeatureInfo', this.showFeatureInfo, this);
            Shared.Dispatcher.on('layers:renderLegend', this.renderLegend, this);
            let administrativeVisibility = Shared.StorageUtil.getItemDict('Administrative', 'transparency');
            if (administrativeVisibility !== null) {
                this.administrativeTransparency = administrativeVisibility;
            }
        },
        fetchAvailableStyles: function (layerName) {
            let select = document.getElementById(`style-${layerName}`);
            const that = this;
            const layer = that.layers[layerName].layer;
            const source = layer.getSource();
            const params = source.getParams();
            const wmsCapabilitiesUrl = `${source.getUrls()[0]}?service=WMS&version=1.3.0&request=GetCapabilities`;

            function styleChangedHandler() {
                const selectedOption = select.options[select.selectedIndex];
                params.STYLES = selectedOption.value;
                layer.getSource().updateParams(params);

                if (that.legends[layerName]) {
                    that.renderLegend(
                        layerName,
                        params.name,
                        source.getUrls()[0],
                        params.layers,
                        false,
                        params.STYLES
                    );
                    const $legendElement = that.getLegendElement(layerName);
                    that.legends[layerName] = $legendElement;
                    if ($legendElement.length > 0) {
                        const selected = Shared.StorageUtil.getItemDict(layerName, 'selected');
                        if (selected) {
                            $legendElement.show();
                            let legendDisplayed = Shared.StorageUtil.getItem('legendsDisplayed');
                            if (legendDisplayed !== false || typeof legendDisplayed === 'undefined') {
                                Shared.Dispatcher.trigger('map:showMapLegends');
                            }
                        }
                    }
                }
            }

            if (!select.disabled) {
                return;
            }

            fetch(wmsCapabilitiesUrl)
                .then((response) => response.text())
                .then((xml) => {
                    select.innerHTML = '';
                    select.disabled = false;
                    const parser = new DOMParser();
                    const xmlDoc = parser.parseFromString(xml, "application/xml");
                    const layers = xmlDoc.getElementsByTagName("Layer");
                    const fetchedStyles = {};
                    for (let i = 0; i < layers.length; i++) {
                        const layerTitle = layers[i].getElementsByTagName("Name")[0].textContent;
                        if (layerTitle === `${layerName}`) {
                            const styles = layers[i].getElementsByTagName("Style");
                            const styleNames = [];
                            for (let j = 0; j < styles.length; j++) {
                                const styleName = styles[j].getElementsByTagName("Name")[0].textContent;
                                const styleTitle = styles[j].getElementsByTagName("Title")[0].textContent;
                                fetchedStyles[styleTitle] = styleName;
                                styleNames.push(styleName);
                            }
                            if (styleNames.length > 1) {
                                select.removeEventListener('change', styleChangedHandler);
                                select.addEventListener('change', styleChangedHandler);
                                let styleKeys = Object.keys(fetchedStyles);
                                let orderedStyles = {};
                                const firstKey = styleKeys.shift();
                                styleKeys.sort();
                                styleKeys.unshift(firstKey);
                                styleKeys.forEach((key) => {
                                    orderedStyles[key] = fetchedStyles[key]
                                });
                                for (const styleKey in orderedStyles) {
                                    let style = orderedStyles[styleKey];
                                    let option = document.createElement('option');
                                    option.text = styleKey;
                                    option.value = style;
                                    select.add(option);
                                }
                            }
                            return styleNames;
                        }
                    }
                })
                .catch((error) => console.error("Error fetching WMS capabilities:", error));
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
        initLayer: function (layer, layerTitle, layerName, visibleInDefault, category = null, source = null, enableStylesSelection = false) {
            layer.set('added', false);
            var layerType = layerName;
            var layerSource = '';
            var layerCategory = '';
            if (layerName.indexOf(this.administrativeKeyword) >= 0) {
                layerType = layerName;
            }
            if (layerName === 'Sites') {
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
                'layerTitle': layerTitle,
                'category': layerCategory,
                'source': layerSource,
                'enableStylesSelection': enableStylesSelection
            };
            if (!visibleInDefault) {
                layer.setVisible(false);
            }
        },
        addBiodiversityLayersToMap: function (map) {
            var self = this;
            // ---------------------------------
            // HIGHLIGHT PINNED LAYER
            // ---------------------------------
            self.highlightPinnedVectorSource = new ol.source.Vector({});
            self.highlightPinnedVector = new ol.layer.Vector({
                source: self.highlightPinnedVectorSource,
                style: function (feature) {
                    var geom = feature.getGeometry();
                    return self.layerStyle.getPinnedHighlightStyle(geom.getType());
                }
            });
            map.addLayer(self.highlightPinnedVector);

            // ---------------------------------
            // HIGHLIGHT LAYER -- MARKER
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
                url: '/bims_proxy/' + geoserverPublicUrl + 'wms',
                params: {
                    LAYERS: locationSiteGeoserverLayer,
                    FORMAT: 'image/png8',
                    viewparams: 'where:' + defaultWMSSiteParameters
                },
                ratio: 1,
                serverType: 'geoserver',
                transition: 0
            };
            self.biodiversitySource = new ol.source.TileWMS(biodiversityLayersOptions);
            self.biodiversityTileLayer = new ol.layer.Tile({
                source: self.biodiversitySource
            });
            self.initLayer(
                self.biodiversityTileLayer,
                'Sites',
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
        convertStyles: function (styles, name) {
            styles['sources'] = {}
            styles['sources'][name] = {
                "type": "vector",
                "data": "",
            }
            styles['name'] = name;
            for (let i = 0; i < styles['layers'].length; i++) {
                styles['layers'][i]['id'] = `${name}-${i}`;
                styles['layers'][i]['source'] = name
                styles['layers'][i]['minzoom'] = 0
            }
            return styles
        },
        addLayersToMap: function (map) {
            var self = this;
            this.map = map;

            var biodiversityOrder = Shared.StorageUtil.getItemDict('Sites', 'order');
            if (biodiversityOrder === null) {
                biodiversityOrder = 0;
            }
            self.orders[0] = 'Sites';
            self.addBiodiversityLayersToMap(map);
            self.renderLayers(false);

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

                        var layerOrder = value['order'] + 1;
                        self.orders[layerOrder] = value['wms_layer_name'];

                        var defaultVisibility = Shared.StorageUtil.getItemDict(
                            value['wms_layer_name'], 'selected');
                        if (defaultVisibility === null) {
                            defaultVisibility = value['default_visibility'];
                        }
                        Shared.StorageUtil.setItemDict(value['wms_layer_name'], 'selected', defaultVisibility);
                        let options = {};
                        let tileLayer = null;
                        let wmsUrl = value.wms_url;
                        if (!value.native_layer_url) {
                            options = {
                                url: '/bims_proxy/' + encodeURI(value.wms_url),
                                params: {
                                    name: value.name,
                                    layers: value.wms_layer_name,
                                    format: value.wms_format,
                                    getFeatureFormat: value.get_feature_format,
                                    STYLES: value.layer_style
                                }
                            }
                            wmsUrl = wmsUrl.replace(/(^\w+:|^)\/\//, '').split('/');
                            if (wmsUrl.length > 0) {
                                wmsUrl = wmsUrl[0];
                            }
                            tileLayer = new ol.layer.Tile({
                                source: new ol.source.TileWMS(options),
                            })
                        } else {
                            let vectorSource = null;
                            if (value.pmtiles) {
                                vectorSource = new olpmtiles.PMTilesVectorSource({
                                  url: value.pmtiles,
                                  attributions: [value.attribution]
                                });
                            } else {
                                vectorSource = new ol.source.VectorTile({
                                    attributions: [value.attribution],
                                    url: value.native_layer_url,
                                    format: new ol.format.MVT(),
                                    STYLES: value.native_layer_style
                                })
                            }
                            tileLayer = new ol.layer.VectorTile({
                                title: value.name,
                                source: vectorSource,
                                STYLES: value.native_layer_style,
                                tileGrid: ol.tilegrid.createXYZ(),
                                declutter: true,
                            })
                            olms.applyStyle(tileLayer, self.convertStyles(value.native_layer_style, value.name), value.name).catch((error) => {
                                console.error('Failed to apply style:', error);
                            });
                        }


                        self.initLayer(
                            tileLayer,
                            value.name,
                            value['wms_layer_name'], defaultVisibility, '', wmsUrl, value['enable_styles_selection']
                        );
                    });

                    // let administrativeOrder = self.administrativeOrder + 1;
                    // self.orders[administrativeOrder] = self.administrativeKeyword;
                    // self.addAdministrativeLayerToMap(data);
                    // Render available layers first because fetching layer from geonode takes time

                    self.renderLayers(true);

                    $('.layer-source').click(function (e) {
                        self.showLayerSource(e.target.attributes["value"].value);
                    });

                    $('.layer-source-style').click(function (e) {
                        self.showLayerStyle(e.target.attributes["value"].value);
                    });

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

                        if (layerName === 'null' ||
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
                            value.title, value.typename, false, category, 'GeoNode'
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
            // this.changeLayerTransparency(this.administrativeKeyword, this.administrativeTransparency);
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
            let needToReloadXHR = true;
            this.toggleLegend(layerName, selected, needToReloadXHR);
        },
        renderSitesLegend: function () {
            let $mapLegend = $('#map-legend');
            if ($mapLegend.find('#site-legend').length > 0) {
                return;
            }
            let html = $(`<div data-name="Sites" id="site-legend" class="legend-row" style="width: 200px"/>`);
            html.append($(`<b>Sites</b><br/>`));
            html.append(_.template($('#fbis-site-legend').html()));
            $mapLegend.prepend(html);
            this.legends['Sites'] = html;

        },
        hideSitesLegend: function () {
            $('#map-legend').find('#site-legend').remove();
        },
        toggleLegend: function (layerName, selected, reloadXHR) {
            // show/hide legend
            try {
                const layer = this.layers[layerName];
                if (!(layer.layer instanceof ol.layer.VectorTile)) {
                    const params = layer.layer.getSource().getParams();
                    if (siteCodeGeneratorMethod === 'fbis' && params.name === 'Rivers') {
                        return;
                    }
                }
            } catch (e) {
                console.error(e)
                return;
            }

            let $legendElement = this.getLegendElement(layerName);
            if (layerName === 'Sites' && this.isBiodiversityLayerLoaded()) {
                if (siteCodeGeneratorMethod === 'fbis') {
                    if (selected) {
                        this.renderSitesLegend();
                    } else {
                        this.hideSitesLegend();
                    }
                }
                $legendElement = this.getLegendElement(layerName);
                if (reloadXHR) {
                    Shared.Dispatcher.trigger('map:reloadXHR');
                }
            }

            if (selected) {
                if (!this.legends[layerName]) {
                    try {
                        const layer = this.layers[layerName];
                        const source = layer.layer.getSource();
                        if (!(layer.layer instanceof ol.layer.VectorTile)) {
                            const params = layer.layer.getSource().getParams();
                            const layers = params.layers || params.LAYERS;
                            const name = params.name || params.NAME;
                            // Draw legend
                            this.renderLegend(
                                layerName,
                                name,
                                source.getUrls()[0],
                                layers,
                                false,
                                params.STYLES
                            );
                            $legendElement = this.getLegendElement(layerName);
                            this.legends[layerName] = $legendElement;
                        } else {
                            this.renderVectorTileLegend(
                                layerName,
                                layerName,
                                layer.layer,
                                false,
                                layer.layer.values_.STYLES.layers
                            );
                            $legendElement = this.getLegendElement(layerName);
                            this.legends[layerName] = $legendElement;
                        }
                    } catch (e) {
                        console.error(e)
                    }
                }
                if ($legendElement.length > 0) {
                    $legendElement.show();
                    let legendDisplayed = Shared.StorageUtil.getItem('legendsDisplayed');
                    if (legendDisplayed !== false || typeof legendDisplayed === 'undefined') {
                        Shared.Dispatcher.trigger('map:showMapLegends');
                    }
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
        renderLegend: function (id, name, url, layer, visibleDefault, style='') {
            if (typeof name === 'undefined') {
                name = id;
            }
            var scr = url + '?request=GetLegendGraphic&format=image/png&width=40&height=40&layer=' + layer;
            if (url.indexOf('.qgs') != -1) {
                scr = url + '&service=WMS&request=GetLegendGraphic&format=image/png&transparent=true&width=40&height=40&layer=' + layer;
            }
            scr += '&STYLE=' + style;
            let html = '<div data-name="' + id + '" class="legend-row"';
            if (!visibleDefault) {
                html += ' style="display: None"'
            }
            let existingLegend = this.getLegendElement(id);
            let content = (
                '<b>' + name + '</b><br>' +
                '<img src="' + scr + '">'
            )
            if (existingLegend.length > 0) {
                existingLegend.html(content)
            } else {
                html += '>' +
                    content + '</div>';
                $('#map-legend').prepend(html);
            }
        },
        renderVectorTileLegend: function (id, name, vectorTileLayer, visibleDefault, styles) {
            if (typeof name === 'undefined') {
                name = id;
            }

            let legendHTML = '<div data-name="' + id + '" class="legend-row"';
            if (!visibleDefault) {
                legendHTML += ' style="display: none;"';
            }

            let content = '<b>' + name + '</b><br>';

            function extractValuesFromFilter(filter) {
                let values = [];
                if (Array.isArray(filter)) {
                    // Check if the filter uses "any" or "all"
                    if (filter[0] === 'any' || filter[0] === 'all') {
                        filter.slice(1).forEach((item) => {
                            if (Array.isArray(item) && item[0] === '==' && item.length === 3) {
                                values.push(item[2]);
                            }
                        });
                    } else if (filter[0] === '==' && filter.length === 3) {
                        values.push(filter[2]);
                    }
                }
                return values;
            }

            // Process each style rule to create legend items
            if (Array.isArray(styles)) {
                styles.forEach((rule) => {
                    if (rule.paint) {
                        const fillColor = rule.paint['fill-color'] || 'transparent';
                        const strokeColor = rule.paint['fill-outline-color'] || 'transparent';
                        const lineColor = rule.paint['line-color'] || 'transparent';
                        const lineWidth = rule.paint['line-width'] || 1;

                        const values = extractValuesFromFilter(rule.filter);

                        if (values.length === 0) {
                            return true;
                        }

                        if (fillColor !== 'transparent') {
                            content += '<div style="display: inline-block; width: 20px; height: 20px; background-color:' + fillColor + '; border: 1px solid ' + strokeColor + '; margin-right: 5px;"></div>';
                        } else if (lineColor !== 'transparent') {
                            content += '<div style="display: inline-block; width: 20px; height: 20px; border-bottom: ' + (lineWidth * 2) + 'px solid ' + lineColor + '; margin-right: 5px;"></div>';
                        }
                        content += values[0] + '<br>';
                    }
                });
            } else {
                content += '<div>No styles available</div>';
            }

            // If an existing legend for this ID exists, update it; otherwise, add a new one
            let existingLegend = this.getLegendElement(id);
            if (existingLegend.length > 0) {
                existingLegend.html(content);
            } else {
                legendHTML += '>' + content + '</div>';
                $('#map-legend').prepend(legendHTML);
            }
        },
        renderLayersSelector: function (key, name, title, visibleInDefault, transparencyDefault, category, source, isFirstTime, enableStylesSelection = false) {
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
                title: title,
                key: key,
                checked: checked,
                transparency_value: transparencyDefault,
                display: layerDisplayed,
                source: source,
                category: category,
                enableStylesSelection: enableStylesSelection
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
                var layerTitle = '';
                var defaultVisibility = false;
                var category = '';
                var source = '';

                if (typeof value !== 'undefined') {
                    layerName = value['layerName'];
                    layerTitle = value['layerTitle'];
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

                self.renderLayersSelector(key, layerName, layerTitle, defaultVisibility, currentLayerTransparency, category, source, isFirstTime, typeof value !== 'undefined' ? value['enableStylesSelection'] : false);
            });

            // RENDER LAYERS
            $.each(reversedOrders, function (key, value) {
                let _layer = self.layers[value]['layer'];
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
                setTimeout(function () {
                    self.initializeLayerSelector();
                }, 500)
                self.refreshLayerOrders();
            }
        },
        showFeatureInfo: function (lon, lat, siteExist = false) {
            // Show feature info from lon and lat
            // Lon and lat coordinates are in EPSG:3857 format

            lon = parseFloat(lon);
            lat = parseFloat(lat);
            const coordinate = ol.proj.transform(
                [lon, lat], 'EPSG:4326', 'EPSG:3857');

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
            const that = this;
            const view = this.map.getView();
            let lastCoordinate = coordinate;
            let featuresInfo = {};

            Shared.GetFeatureRequested = true;
            Shared.Dispatcher.trigger('map:showPopup', coordinate,
                '<div class="info-popup popup-loading"> Fetching... </div>');
            $.each(this.layers, function (layer_key, layer) {
                if (coordinate !== lastCoordinate) {
                    return;
                }
                if (layer['layer'].getVisible()) {
                    try {
                        if (layer['layer'] instanceof ol.layer.VectorTile) {
                            const pixel = that.map.getPixelFromCoordinate(coordinate);
                            that.map.forEachFeatureAtPixel(pixel, function (feature, _layer) {
                                if (_layer === layer['layer']) {
                                    const properties = feature.getProperties();
                                    delete properties.geometry;

                                    if (!$.isEmptyObject(properties)) {
                                        featuresInfo[layer_key] = {
                                            'layerName': layer['layerTitle'],
                                            'properties': properties,
                                            'layerAttr': null,
                                            'layerId': null,
                                            'document': null,
                                            'documentTitle': null
                                        };
                                    }
                                }
                            })
                        } else {
                            const queryLayer = layer['layer'].getSource().getParams()['layers'];
                            if (queryLayer.indexOf('location_site_view') > -1) {
                                return true;
                            }
                            const getFeatureFormat = layer['layer'].getSource().getParams()['getFeatureFormat'];
                            const layerName = layer['layer'].getSource().getParams()['name'];
                            let layerSource = layer['layer'].getSource().getFeatureInfoUrl(
                                coordinate,
                                view.getResolution(),
                                view.getProjection(),
                                {'INFO_FORMAT': getFeatureFormat}
                            );
                            layerSource += '&QUERY_LAYERS=' + queryLayer;
                            Shared.GetFeatureXHRRequest.push($.ajax({
                                type: 'POST',
                                url: '/get_feature/',
                                data: {
                                    'layerSource': layerSource,
                                    'layerName': layer.layerName
                                },
                                success: function (result) {
                                    // process properties
                                    const data = result['feature_data'];
                                    if (coordinate !== lastCoordinate || !data) {
                                        return;
                                    }
                                    let linesData = data.split("\n");
                                    let properties = {};

                                    // reformat plain text to be dictionary
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
                                        'layerName': layer['layerTitle'],
                                        'properties': properties,
                                        'layerAttr': result['layer_attr'],
                                        'layerId': result['layer_id'],
                                        'document': result['document'],
                                        'documentTitle': result['document_title']
                                    };
                                },
                            }));
                        }
                    } catch (err) {
                        console.error(err)
                    }
                }
            });
            Promise.all(Shared.GetFeatureXHRRequest).then(() => {
                if (Object.keys(featuresInfo).length > 0) {
                    that.renderFeaturesInfo(featuresInfo, coordinate);
                } else {
                    Shared.Dispatcher.trigger('map:closePopup');
                }
                Shared.GetFeatureXHRRequest = [];
            }).catch((err) => {
                if (Shared.GetFeatureXHRRequest.length > 0) {
                    Shared.Dispatcher.trigger('map:showPopup', coordinate,
                        '<div class="info-popup popup-error">Failed to fetch feature info</div>');
                    Shared.GetFeatureXHRRequest = [];
                }
            });
        },
        downloadFilteredLayerData: function (layerFilter, layerId, layerName, $button) {
            let _layerFilter = layerFilter;
            if (layerFilter.endsWith('.0')) {
                _layerFilter = layerFilter.replace('.0', '')
            }
            $.get(`/api/download-layer-data/${layerId}/${_layerFilter}/`, function(response) {
                const data = response['data'];
                if (data) {
                    const csvData = [
                        Object.keys(data).join(','),
                        Object.values(data).join(','),
                        ''
                    ].join('\n')
                    // CSV file
                    let csvFile = new Blob([csvData], {type: "text/csv"});
                    // Download link
                    let downloadLink = document.createElement("a");
                    // File name
                    downloadLink.download = `${layerName}-${layerFilter}.csv`
                    // Create a link to the file
                    downloadLink.href = window.URL.createObjectURL(csvFile);
                    // Hide download link
                    downloadLink.style.display = "none";
                    // Add the link to DOM
                    document.body.appendChild(downloadLink);
                    // Click download link
                    downloadLink.click();
                }

                $button.removeAttr("disabled");
            })
        },
        hideAll: function (e) {
            if ($(e.target).data('visibility')) {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-down');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-up');
                $(e.target).nextAll().hide();
                $(e.target).data('visibility', false)
            } else {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-up');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-down');
                $(e.target).nextAll().show();
                $(e.target).data('visibility', true)
            }
        },
        showWetlandDashboard: function (coordinateStr) {
            let requestId = Math.random().toString(36).substr(2, 9);
            let self = this;
            self.currentWetlandRequestId = requestId;
            let coords = coordinateStr.split(',').map(function(item) {
                return parseFloat(item);
            });
            let convertedCoords = ol.proj.transform(coords, 'EPSG:3857', 'EPSG:4326');

            Shared.Dispatcher.trigger('sidePanel:toggleLoading', true);
            Shared.Dispatcher.trigger('sidePanel:openSidePanel');
            if (Shared.WetlandDashboardXHRRequest) {
                Shared.WetlandDashboardXHRRequest.abort();
                Shared.WetlandDashboardXHRRequest = null;
            }

            // NewWetlandRequestInitiated
            function fetchWetlandData() {

                Shared.WetlandDashboardXHRRequest = $.get({
                    url: `/api/wetland-data/${convertedCoords[0]}/${convertedCoords[1]}/`,
                    dataType: 'json',
                    success: function (data) {
                        if (self.currentWetlandRequestId !== requestId) {
                            return;
                        }
                        Shared.Dispatcher.trigger('sidePanel:toggleLoading', false);
                        let $detailWrapper = $('<div style="padding-left: 0;"></div>');

                        if (data.hasOwnProperty('message')) {
                            if (data['message'] === 'layer not found') {
                                $detailWrapper.html('<div>Wetland data not found</div>')
                                return;
                            }
                        }

                        let siteDetailsTemplate = _.template($('#wetland-side-panel-dashboard').html());
                        $detailWrapper.html(siteDetailsTemplate(data));

                        $detailWrapper.find('.search-results-total').click(self.hideAll);
                        $detailWrapper.find('.search-results-total').click();

                        Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', 'Wetland Dashboard');
                        Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $detailWrapper);

                        if (data.task_status.state !== 'SUCCESS') {
                            setTimeout(function() {
                                // Ensure no new request has been initiated
                                if (!Shared.NewWetlandRequestInitiated) {
                                    fetchWetlandData();
                                }
                            }, 5000);
                        }
                    }
                })
                Shared.NewWetlandRequestInitiated = false;
            }

            Shared.NewWetlandRequestInitiated = true;

            fetchWetlandData();
        },
        renderFeaturesInfo: function (featuresInfo, coordinate) {
            var that = this;
            let tabs = '<ul class="nav nav-tabs">';
            let content = '';
            $.each(featuresInfo, function (key_feature, feature) {
                var layerName = feature['layerName'];
                let contentId = `info-${key_feature.replace(':', '-')}`;
                if (layerName.indexOf(that.administrativeKeyword) >= 0) {
                    layerName = that.administrativeKeyword;
                    key_feature = 'administrative';
                }
                tabs += '<li ' +
                    'role="presentation" class="info-wrapper-tab"  ' +
                    'title="' + layerName + '" ' +
                    'data-tab="info-' + key_feature + '">' +
                    layerName + '</li>';
                content += '<div class="info-wrapper" data-tab="info-' + key_feature + '" id="' + contentId + '">';

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

            $.each(featuresInfo, function (key_feature, feature) {
                let layerAttr = feature['layerAttr'];
                let layerName = feature['layerName'];
                let document = feature['document'];
                let documentTitle = feature['documentTitle'] ? feature['documentTitle'] : 'document';
                let contentId = `info-${key_feature.replace(':', '-')}`;
                if (document) {
                    let downloadDoc = $(`<br/><a href="${document}" class="btn btn-xs secondary-accent-background" download>Download ${documentTitle}</a>`);
                    $(`#${contentId}`).prepend(downloadDoc);
                }
                if (layerAttr) {
                    let downloadButton = $('<button class="btn btn-xs btn-primary">Download data</button>');
                    downloadButton.click(function () {
                        $(this).attr("disabled", true);
                        that.downloadFilteredLayerData(feature['properties'][layerAttr], feature['layerId'], layerName, $(this));
                    });
                    $(`#${contentId}`).prepend(downloadButton);
                }
                if (key_feature === that.wetlandLayer) {
                    let wetlandDashboardButton = $('<div class="btn btn-xs btn-primary wetland-dashboard">Wetland Dashboard</div>');
                    wetlandDashboardButton.click(function() {
                        that.showWetlandDashboard('' + coordinate);
                    });
                    $(`#${contentId}`).prepend(wetlandDashboardButton);
                }
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
            } else if (layerKey !== this.administrativeKeyword) {
                this.getLayerAbstract(layerKey);
            }
        },
        showLayerStyleOptions: function (layerKey) {
            let layerSourceContainer = $('div.layer-source-style-container[value="' + layerKey + '"]');
            if (layerSourceContainer.is(':visible')) {
                layerSourceContainer.slideUp(200);
            } else {
                layerSourceContainer.slideDown(200);
                // Fetch styles from geoserver
                this.fetchAvailableStyles(layerKey);
            }
        },
        showLayerStyle: function (layerKey) {
            if (Object.keys(this.layers).length === 0) {
                return false;
            }
            this.showLayerStyleOptions(layerKey);
        },
        getLayerAbstract: function (layerKey) {
            let layerProvider = '';
            let layerName = '';
            let layerSourceContainer = $('div.layer-source-info[value="' + layerKey + '"]');
            let fetching = layerSourceContainer.data('fetching');
            if (fetching) {
                if (layerSourceContainer.is(':visible')) {
                    layerSourceContainer.slideUp(200);
                } else {
                    layerSourceContainer.slideDown(200);
                }
                return;
            }
            layerSourceContainer.data('fetching', true);
            layerSourceContainer.html('<div style="width: 100%; height: 50px; text-align: center; padding-top:18px;">Fetching...</div>');
            layerSourceContainer.slideDown(200);

            if (layerKey.indexOf(":") > 0) {
                layerProvider = layerKey.split(":")[0];
                layerName = layerKey.split(":")[1];
            } else {
                layerProvider = layerKey;
                layerName = layerKey;
            }
            let url_provider = layerProvider;
            let url_key = layerName;
            let source = this.layers[layerKey].source
            var abstract_result = "";
            $.ajax({
                type: 'GET',
                url: `/bims_proxy/http://${source}/geoserver/${url_provider}/${url_key}/wms?request=getCapabilities`,
                dataType: `xml`,
                success: function (response) {
                    let xml_response, parser, xmlDoc;
                    xml_response = response['documentElement']['innerHTML'];
                    xml_response = xml_response.replace(/[\r\n]*/g, "");
                    xml_response = xml_response.replace("\\n", "");
                    xml_response = '<document>' + xml_response.replace(" ", "") + '</document>';

                    parser = new DOMParser();
                    xmlDoc = parser.parseFromString(xml_response, 'text/xml');
                    try {
                        abstract_result = xmlDoc.getElementsByTagName("Abstract")[2].childNodes[0].nodeValue;
                    } catch (e) {
                        abstract_result = "Abstract information unavailable.";
                    }
                },
                error(err) {
                    abstract_result = "Abstract information unavailable.";
                },
                complete() {
                    layerSourceContainer.html(`
                        <div class="layer-abstract cancel-sortable">
                            ` + abstract_result + `
                        </div>`);
                }
            })
        },
        initializeLayerSelector: function () {
            let self = this;
            this.layerSelector = $('#layers-selector');
            this.layerSelector.sortable({cancel: '.cancel-sortable'});
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
                } else {
                    if (layerName === 'Sites') {
                        self.changeLayerOder(layerName, 0)
                    }
                }
            });
            if (self && self.layerSelector) {
                self.layerSelector.trigger('sortupdate');
            } else {
                setTimeout(function () {
                    self.layerSelector.trigger('sortupdate');
                }, 600)
            }
        }
    })
});
