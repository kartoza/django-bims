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
        layers: {},
        layerGroups: {},
        initialLoadBiodiversityLayersToMap: false,
        orders: {},
        layerSelector: null,
        currentWetlandRequestId: null,
        legends: {},
        wetlandLayer: 'kartoza:nwm6_beta_v3_20230714',
        initialize: function () {
            this.layerStyle = new LayerStyle();
            Shared.Dispatcher.on('layers:showFeatureInfo', this.showFeatureInfo, this);
            Shared.Dispatcher.on('layers:renderLegend', this.renderLegend, this);
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
        initLayer: function (
            layer, layerData,
            category = null, source = null) {
            layer.set('added', false);

            let layerTitle = layerData['name'];
            let layerName = layerData['wms_layer_name'];
            let enableStylesSelection = layerData['enable_styles_selection'] || false;

            let layerType = layerName;
            let layerSource = '';
            let layerCategory = '';
            if (layerName === 'Sites') {
                layerType = layerName;
                layerTitle = layerName;
            }
            let defaultVisibility = Shared.StorageUtil.getItemDict(
                layerName, 'selected');
            if (defaultVisibility === null) {
                defaultVisibility = layerData['default_visibility'];
            }
            Shared.StorageUtil.setItemDict(layerData['wms_layer_name'], 'selected', defaultVisibility);

            if (category) {
                layerCategory = category;
            }
            if (source) {
                layerSource = source;
            }
            this.layers[layerType] = {
                'layer': layer,
                'visibleInDefault': defaultVisibility,
                'layerName': layerName,
                'layerTitle': layerTitle,
                'category': layerCategory,
                'source': layerSource,
                'enableStylesSelection': enableStylesSelection
            };
            if (!defaultVisibility) {
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

            let biodiversityLayerData = {
                'title': 'Sites',
                'wms_layer_name': 'Sites',
                'default_visibility': true
            }
            self.initLayer(
                self.biodiversityTileLayer,
                biodiversityLayerData,
            );

            if (!self.initialLoadBiodiversityLayersToMap) {
                self.initialLoadBiodiversityLayersToMap = true;
            }
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

            function _createLayer(layerData) {
                let source = layerData.wms_url;
                let tileLayer = null;
                let category = '';
                if (!layerData.native_layer_url) {
                    options = {
                        url: '/bims_proxy/' + encodeURI(layerData.wms_url),
                        params: {
                            name: layerData.name,
                            layers: layerData.wms_layer_name,
                            format: layerData.wms_format,
                            getFeatureFormat: layerData.get_feature_format,
                            STYLES: layerData.layer_style,
                            displayInLayerSwitcher: true,
                        }
                    }
                    source = source.replace(/(^\w+:|^)\/\//, '').split('/');
                    if (source.length > 0) {
                        source = source[0];
                    }
                    tileLayer = new ol.layer.Tile({
                        source: new ol.source.TileWMS(options),
                    })
                } else {
                    let vectorSource = null;
                    category = 'nativeLayer';
                    source = layerData.native_layer_abstract ? layerData.native_layer_abstract : '-';
                    if (layerData.pmtiles) {
                        vectorSource = new olpmtiles.PMTilesVectorSource({
                          url: layerData.pmtiles,
                          attributions: [layerData.attribution]
                        });
                    } else {
                        vectorSource = new ol.source.VectorTile({
                            attributions: [layerData.attribution],
                            url: layerData.native_layer_url,
                            format: new ol.format.MVT(),
                            STYLES: layerData.native_layer_style
                        })
                    }
                    tileLayer = new ol.layer.VectorTile({
                        source: vectorSource,
                        STYLES: layerData.native_layer_style,
                        tileGrid: ol.tilegrid.createXYZ(),
                        declutter: true,
                    })
                    olms.applyStyle(tileLayer, self.convertStyles(
                        layerData.native_layer_style,
                        layerData.name), layerData.name).catch((error) => {
                        console.error('Failed to apply style:', error);
                    });
                }

                return {
                    'tile': tileLayer,
                    'category': category,
                    'source': source
                }
            }

            $.ajax({
                type: 'GET',
                url: listNonBiodiversityLayerAPIUrl,
                dataType: 'json',
                success: function (data) {
                    let listNonBioHash = Shared.StorageUtil.getItem('listNonBiodiversity');
                    let hashCurrentList = Shared.StorageUtil.hashItem(JSON.stringify(data));
                    if (!listNonBioHash || listNonBioHash !== hashCurrentList) {
                        Shared.StorageUtil.clear();
                        Shared.StorageUtil.setItem(
                            'listNonBiodiversity',
                            hashCurrentList);
                    }
                    $.each(data, function (index, value) {
                        let layerOrder = value['order'] + 1;

                        if (value['type'] === 'LayerGroup') {
                            self.orders[layerOrder] = value['name'];
                            self.layerGroups[value['name']] = value;
                            $.each(value['layers'], function (idx, layer) {
                                let _layer = _createLayer(layer);
                                self.initLayer(
                                    _layer['tile'],
                                    layer,
                                    _layer['category'],
                                    _layer['source']
                                );
                            })
                            return;
                        }

                        self.orders[layerOrder] = value['wms_layer_name'];
                        let _layer = _createLayer(value);
                        self.initLayer(
                            _layer['tile'],
                            value,
                            _layer['category'],
                            _layer['source']
                        );
                    });

                    self.renderLayers();
                    $('.layer-source').click(function (e) {
                        self.showLayerSource(e.target.attributes["value"].value);
                    });
                    $('.layer-source-style').click(function (e) {
                        self.showLayerStyle(e.target.attributes["value"].value);
                    });

                },
                error: function (err) {
                }
            });
        },
        changeLayerVisibility: function (layerName, visible) {
            if (Object.keys(this.layers).length === 0) {
                return false;
            }
            this.layers[layerName]['layer'].setVisible(visible);
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
            if (layerName === 'Sites') {
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
        renderVectorTileLegend: function (
            id,
            name = id,
            vectorTileLayer = undefined,
            visible = true,
            styles = []
        ) {
            const $legendHost   = $('#map-legend');
            const legendRowSel  = `.legend-row[data-name="${id}"]`;
            let attributeField = '';

            function getFilteredValues(filter) {
                let result = { field: null, values: [] };
                function walk(expr) {
                    if (!Array.isArray(expr)) { return; }
                    let op   = expr[0];
                    let rest = expr.slice(1);
                    if (op === 'all' || op === 'any') {
                        for (var i = 0; i < rest.length; i++) { walk(rest[i]); }
                    }
                    else if (op === '==' || op === 'in' || op === '!in') {
                        let field = rest[0];
                        if (field === '$type') { return; }
                        if (!result.field) { result.field = field; }
                        if (op === '==') {
                            result.values.push(rest[1]);
                        } else {
                            result.values = result.values.concat(rest.slice(1));
                        }
                    }
                }
                walk(filter);
                return result;
            }

            function makeSwatch(fillColor, strokeColor = 'transparent') {
                const div = document.createElement('div');
                div.className = 'legend-swatch';
                div.style.cssText = `
                    width: 16px;
                    height: 16px;
                    margin-right: 6px;
                    background-color: ${fillColor};
                    border: 1px solid ${strokeColor};
                    flex-shrink: 0;
                `;
                return div;
            }

            const fragment = document.createDocumentFragment();
            const title    = document.createElement('strong');
            title.textContent = name;
            fragment.appendChild(title);
            fragment.appendChild(document.createElement('br'));
             if (Array.isArray(styles) && styles.length > 0) {
                styles.forEach(rule => {
                    const paint = rule.paint || {};
                    const fillColor = paint['fill-color'] || paint['circle-color'] || paint['line-color'] || 'transparent';
                    const strokeColor = paint['fill-outline-color'] || paint['circle-stroke-color'] || paint['line-color'] ||'transparent';

                    const info = getFilteredValues(rule.filter);
                    if (!attributeField) {
                        attributeField = info.field ? info.field : attributeField;
                    }
                    if ((!info.field || info.values.length === 0) &&
                        fillColor !== 'transparent') {
                        const geomType = (function unpack(expr) {
                            if (!Array.isArray(expr)) { return null; }
                            if (expr[0] === '==' && expr[1] === '$type') {
                                return expr[2];
                            }
                            for (let i = 1; i < expr.length; i++) {
                                const t = unpack(expr[i]);
                                if (t) { return t; }
                            }
                            return null;
                        })(rule.filter) || 'Geometry';
                        const item = document.createElement('div');
                        item.className = 'legend-item';
                        const swatch = makeSwatch(fillColor, strokeColor);
                        item.appendChild(swatch);
                        item.appendChild(document.createTextNode(geomType));
                        fragment.appendChild(item);
                        return;
                    }
                    if (info.values.length === 0 || fillColor === 'transparent') {
                        return;
                    }
                    info.values.forEach(value => {
                        const item = document.createElement('div');
                        item.className = 'legend-item';
                        item.dataset.value = value;

                        const swatch = makeSwatch(fillColor, strokeColor);
                        const label = document.createTextNode(value);

                        item.appendChild(swatch);
                        item.appendChild(label);
                        fragment.appendChild(item);
                    });
                });
            } else {
                fragment.append('No styles available');
            }

            let $row = $(legendRowSel);
            if ($row.length === 0) {
                $row = $('<div>', {class: 'legend-row', 'data-name': id}).appendTo($legendHost);
            } else {
                $row.empty();
            }
            $row.css('display', visible ? '' : 'none');
            $row.append(fragment);
            const that = this;

            if (attributeField) {
                $row.on('mouseenter', '.legend-item', function () {
                    let hoveredValue = $(this).data('value');

                    if (!vectorTileLayer.get('origStyle')) {
                        vectorTileLayer.set('origStyle', vectorTileLayer.getStyle() || null);
                    }
                    var origStyle = vectorTileLayer.get('origStyle');

                    var highlightStyle = function (feature, resolution) {
                        var base = (typeof origStyle === 'function')
                            ? origStyle.call(this, feature, resolution)
                            : origStyle;
                        var styles = (Array.isArray(base) ? base : [base]).filter(Boolean);
                        if (!styles.length) { return styles; }
                        var isMatch = (feature.get(attributeField) === hoveredValue);
                        styles = styles.map(function (s) {
                            var sty = s.clone();
                            if (isMatch) {
                                var stroke = sty.getStroke();
                                if (!stroke) {
                                    stroke = new ol.style.Stroke({ color: '#ffff00', width: 3 });
                                    sty.setStroke(stroke);
                                } else {
                                    stroke.setColor('#ffff00');
                                    stroke.setWidth(3);
                                }
                            }
                            return sty;
                        });

                        return styles;
                    };
                    vectorTileLayer.setStyle(highlightStyle);
                    that.map.getTargetElement().style.cursor = 'pointer';
                });

                $row.on('mouseleave', '.legend-item', function () {
                    if (vectorTileLayer.get('origStyle')) {
                        vectorTileLayer.setStyle(vectorTileLayer.get('origStyle'));
                    }
                    that.map.getTargetElement().style.cursor = '';
                });
            }
        },
        renderLayerGroup: function (layerGroup) {
            let self = this;
            let id = 'layerGroup_' + layerGroup['id'];
            let name = layerGroup['name'];
            let checked = '';
            const allChildren = layerGroup['layers'];
            const checkedChildren = allChildren.filter(function (layer) {
                const layerObj = self.layers[layer['name']];
                return layerObj && layerObj.visibleInDefault;
            });
            if (checkedChildren.length === 0) {
                checked = '';
            } else if (checkedChildren.length === allChildren.length) {
                checked = 'checked'
            } else {
                checked = 'indeterminate'
            }
            let rowTemplate = _.template($('#layer-group-row').html());
            let $rowTemplate = $(rowTemplate({
                id: id,
                name: name,
                title: name,
                key: id,
                checked: checked,
                opacity: 100
            }));
            if (checked === 'indeterminate') {
                $rowTemplate.find('.layer-group-input').prop('indeterminate', true);
            }
            $rowTemplate.prependTo('#layers-selector');

            $rowTemplate.find('.toggle-group-children').on('click', function () {
                const $btn = $(this);
                const $icon = $btn.find('i');
                const $target = $($btn.data('target'));
                $target.slideToggle(150);
                $icon.toggleClass('fa-chevron-down fa-chevron-up');
            });

            let currentLayerTransparency = null;

            $.each(allChildren, function (idx, layer) {
                let layerName = layer['name'];
                let layerData = self.layers[layer['name']];
                let layerTransparency = Shared.StorageUtil.getItemDict(layerName, 'transparency');
                if (layerTransparency !== null) {
                    currentLayerTransparency = layerTransparency * 100;
                    self.changeLayerTransparency(layerName, layerTransparency);
                } else {
                    currentLayerTransparency = 100;
                }
                self.renderLayersSelector(
                    layer['wms_layer_name'], layer['name'], layer['name'], layerData['visibleInDefault'],
                    currentLayerTransparency, '', layer['native_layer_abstract'],
                    layer['enable_styles_selection'],
                    '#children_' + id
                );
            });
            $(`#children_${id}`).find('.drag-handle').css('visibility', 'hidden');
            setTimeout(function () {
                self.refreshGroupSlider($(`#children_${id}`));
            }, 100)
        },
        renderLayersSelector: function (key, name, title,
                                        visibleInDefault, transparencyDefault, category, source,
                                        enableStylesSelection = false,
                                        container = '#layers-selector') {
            if ($('.layer-selector-input[value="' + key + '"]').length > 0) {
                return
            }
            let self = this;
            let mostTop = 'Sites';
            let checked = '';
            if (visibleInDefault) {
                checked += 'checked';
            }
            if (name === mostTop) {
                name = '<b>' + name + '</b>';
            }
            let layerSelectorSearch = Shared.StorageUtil.getItem('layerSelectorSearch');
            let layerDisplayed = 'block';
            if (layerSelectorSearch) {
                if (name.toLowerCase().indexOf(layerSelectorSearch.toLowerCase()) === -1) {
                    layerDisplayed = 'none';
                }
            }
            let layerId = name;
            if (!source) {
                source = '';
            }
            if (!category) {
                category = '';
            }
            let rowTemplate = _.template($('#layer-selector-row').html());
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
            $rowTemplate.prependTo(container);
            let needToReloadXHR = false;
            self.toggleLegend(key, visibleInDefault, needToReloadXHR);
        },
        refreshGroupSlider: function ($childSlider) {
            const $childrenBox = $childSlider.closest('[id^="children_"]');
            if ($childrenBox.length === 0) return;
            const groupId = $childrenBox.attr('id').replace('children_', '');
            const $groupSlider = $(`.layer-transparency[data-group="${groupId}"]`);
            if ($groupSlider.length === 0) return;
            const values = $childrenBox.find('.layer-transparency')
                .not('[data-group="true"]')
                .map(function () { return $(this).slider('value'); })
                .get();
            if (!values.length) return;
            const min = Math.min.apply(null, values);
            const max = Math.max.apply(null, values);
            const mixed = min !== max;
            const newVal = mixed ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : values[0];
            $groupSlider.slider('value', newVal);
            $groupSlider.toggleClass('mixed-transparency', mixed);
        },
        changeLayerTransparency: function (layername, opacity) {
            let self = this;
            if (!Object.keys(this.layers).length) return false;
            if (this.layerGroups.hasOwnProperty(layername)) {
                $.each(this.layerGroups[layername].layers, function (_, layer) {
                    self.layers[layer.name].layer.setOpacity(opacity);
                });
                return true;
            }
            this.layers[layername].layer.setOpacity(opacity);
        },
        renderTransparencySlider: function () {
            let self = this;
            $('#layers-selector').find('.layer-transparency').each(function () {
                const $slider = $(this);
                $slider.slider({
                    range: 'max',
                    min: 1,
                    max: 100,
                    value: $slider.data('value'),
                    slide(event, ui) {
                        const isGroup = $slider.data('group');
                        const $label = isGroup
                            ? $slider.closest('li').find('.layer-selector-name')
                            : $slider.closest('li').find('.layer-selector-input');
                        const layerKey = isGroup ? $label.html() : $label.val();
                        self.changeLayerTransparency(layerKey, ui.value / 100);
                        if (isGroup) {
                            const groupId = $slider.closest('li').find('.layer-group-input').val();
                            $(`#children_${groupId}`).find('.layer-transparency').not('[data-group="true"]').each(function () {
                                $(this).slider('value', ui.value);
                            });
                            $slider.toggleClass('mixed-transparency', false);
                        } else {
                            self.refreshGroupSlider($slider);
                        }
                    },
                    stop(event, ui) {
                        const isGroup = $slider.data('group');
                        if (isGroup) {
                            const groupId = $slider.closest('li').find('.layer-group-input').val();
                            $(`#children_${groupId}`).find('.layer-selector-input').each(function () {
                                Shared.StorageUtil.setItemDict($(this).val(), 'transparency', ui.value / 100);
                            });
                            $slider.toggleClass('mixed-transparency', false);
                        } else {
                            const $label = $slider.closest('li').find('.layer-selector-input');
                            const layerKey = $label.length ? $label.val() : 'Sites';
                            Shared.StorageUtil.setItemDict(layerKey, 'transparency', ui.value / 100);
                            self.refreshGroupSlider($slider);
                        }
                    }
                });
            });
        },
        renderLayers: function () {
            let self = this;
            let savedOrders = $.extend({}, self.orders);

            // Reverse orders
            let reversedOrders = savedOrders;
            reversedOrders = [];
            $.each(savedOrders, function (key, value) {
                reversedOrders.unshift(value);
            });

            $.each(reversedOrders, function (index, key) {
                let value = self.layers[key];

                if (!value) {
                    if (self.layerGroups[key]) {
                        self.renderLayerGroup(
                            self.layerGroups[key],
                        )
                        $.each(self.layerGroups[key]['layers'], function (key, value) {
                            let layerName = value['name'];
                            if (!self.layers[layerName]) {
                                return
                            }
                            let _layer = self.layers[layerName]['layer'];
                            if (!_layer.get('added')) {
                                _layer.set('added', true);
                                self.map.addLayer(_layer);
                            }
                        });
                        return
                    }
                }

                let layerName = '';
                let layerTitle = '';
                let defaultVisibility = false;
                let category = '';
                let source = '';

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

                let currentLayerTransparency = 100;
                // Get saved transparency data from storage
                let itemName = key;
                let layerTransparency = Shared.StorageUtil.getItemDict(itemName, 'transparency');
                if (layerTransparency !== null) {
                    currentLayerTransparency = layerTransparency * 100;
                    self.changeLayerTransparency(itemName, layerTransparency);
                } else {
                    currentLayerTransparency = 100;
                }

                self.renderLayersSelector(
                    key, layerName, layerTitle, defaultVisibility,
                    currentLayerTransparency, category, source,
                    typeof value !== 'undefined' ? value['enableStylesSelection'] : false);
            });

            // RENDER LAYERS
            $.each(reversedOrders, function (key, value) {
                if (!self.layers[value]) {
                    return
                }
                let _layer = self.layers[value]['layer'];
                if (!_layer.get('added')) {
                    _layer.set('added', true);
                    self.map.addLayer(_layer);
                }
            });
            self.renderTransparencySlider();

            $('.layer-selector-input').change(function (e) {
                const input = $(e.target);
                const isChecked = input.is(':checked');
                self.selectorChanged(input.val(), isChecked);

                const parentDiv = input.closest('[id^="children_"]');
                if (parentDiv.length === 0) return;

                const groupId = parentDiv.attr('id').replace('children_', '');
                const groupCheckbox = $(`.layer-group-input[value="${groupId}"]`);
                if (groupCheckbox.length === 0) return;

                const allChildren = parentDiv.find('.layer-selector-input');
                const checkedChildren = allChildren.filter(':checked');

                if (checkedChildren.length === 0) {
                    groupCheckbox.prop('indeterminate', false).prop('checked', false);
                } else if (checkedChildren.length === allChildren.length) {
                    groupCheckbox.prop('indeterminate', false).prop('checked', true);
                } else {
                    groupCheckbox.prop('indeterminate', true).prop('checked', false);
                }
            });
            $('.layer-group-input').change(function (e) {
                const layerGroupChecked = $(e.target).is(':checked');
                const layerGroupId = $(e.target).val();
                const layerName = $(e.target).parent().find('.layer-selector-name').html();
                const children = $(`#children_${layerGroupId}`).find('.layer-selector-input');

                Shared.StorageUtil.setItemDict(layerName, 'selected', layerGroupChecked);

                $.each(children, function (key, value) {
                    $(value).prop('checked', layerGroupChecked).trigger('change');
                })
            });
            setTimeout(function () {
                self.initializeLayerSelector();
            }, 500)
            self.refreshLayerOrders();
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
                    let csvFile = new Blob([csvData], {type: "text/csv"});
                    let downloadLink = document.createElement("a");
                    downloadLink.download = `${layerName}-${layerFilter}.csv`
                    downloadLink.href = window.URL.createObjectURL(csvFile);
                    downloadLink.style.display = "none";
                    document.body.appendChild(downloadLink);
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
            } else {
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
            let isLayerGroup = this.layerGroups.hasOwnProperty(layerKey);
            let category = isLayerGroup ? 'layerGroup' : this.layers[layerKey].category;
            let source = isLayerGroup ? this.layerGroups[layerKey].description : this.layers[layerKey].source;
            let abstract_result = "";

            if (category === 'nativeLayer' || category === 'layerGroup') {
                abstract_result = source;
                if (!abstract_result || abstract_result === '-') {
                    abstract_result = "Abstract information unavailable.";
                }
                layerSourceContainer.html(`
                    <div class="layer-abstract cancel-sortable">
                        ` + abstract_result + `
                    </div>`);
                return;
            }

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
                $($layerSelectorInput.get()).each(function (index, value) {
                    let layerName = $(value).val();
                    Shared.StorageUtil.setItemDict(layerName, 'order', parseInt(index));
                });
            });
        },
        changeLayerOrder: function (key, order) {
            let $row = $('.sortable-group[data-layer-title="' + key + '"]');
            if (!$row.length) {
                $row = $('.layer-selector-input[value="' + key + '"]').closest('li');
            }
            if (!$row.length) return;
            let $rows = $('#layers-selector > li');
            if (order > $rows.length - 1) order = $rows.length - 1;
            if (order <= 0) {
                $row.insertBefore($rows.get(0));
            } else {
                $row.insertAfter($rows.get(order - 1));
            }
        },
        refreshLayerOrders: function () {
            let self = this;
            let seen = {};
            let rows = [];
            $('#layers-selector > li').each(function () {
                let $li = $(this);
                let key, order;
                let isGroup = false;
                if ($li.hasClass('sortable-group')) {
                    key = $li.find('.layer-selector-name').html();
                    isGroup = true;
                } else {
                    key = $li.find('.layer-selector-input').val();
                    for (const [, g] of Object.entries(self.layerGroups)) {
                        if (g.layers.find(l => l.name === key)) {
                            key = g.name;
                            break;
                        }
                    }
                }
                if (seen[key]) return;
                seen[key] = true;
                if (isGroup) {
                    order = Shared.StorageUtil.getItemDict(self.layerGroups[key]['layers'][0].name, 'order');
                } else {
                    order = Shared.StorageUtil.getItemDict(key, 'order');
                }
                rows.push({ key: key, order: order !== null ? parseInt(order) : 9999 });
            });
            rows.sort(function (a, b) {
                return a.order - b.order;
            });
            $.each(rows, function (index, item) {
                item.order = index;
            });
            $.each(rows, function (_, item) {
                self.changeLayerOrder(item.key, item.order);
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