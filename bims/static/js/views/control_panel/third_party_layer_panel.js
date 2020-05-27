define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery', 'ol'], function (Shared, Backbone, _, jqueryUi, $, ol) {
    return Backbone.View.extend({
        template: _.template($('#third-party-layer-panel-template').html()),
        isEmpty: true,
        layer: null,
        source: null,
        displayed: false,
        miniSASSSelected: false,
        inWARDSelected: false,
        fetchingInWARDSData: false,
        inWARDSStationsUrl: "/proxy/?url=http://inwards.award.org.za/app_json/wq_stations.php",
        events: {
            'click .close-button': 'closeClicked',
            'click .update-search': 'updateSearch',
            'change .mini-sass-check': 'toggleMiniSASSLayer',
            'change .inward-check': 'toggleInward'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.map = options.map;
            this.addMiniSASSLayer();
            this.addInWARDSLayer();
            Shared.Dispatcher.on('third_party_layers:showFeatureInfo', this.showFeatureInfo, this);
        },
        inWARDSStyleFunction: function (feature) {
            let properties = feature.getProperties();
            let color = 'gray';
            if (properties['color']) {
                color = properties['color'];
            } else {
                color = '#C6401D';
            }
            let image = new ol.style.Circle({
                radius: 5,
                fill: new ol.style.Fill({color: color})
            });
            return new ol.style.Style({
                image: image
            });
        },
        addInWARDSLayer: function () {
            this.inWARDSLayer = new ol.layer.Vector({
                source: null,
                style: this.inWARDSStyleFunction
            });
            this.inWARDSLayer.setVisible(false);
            this.map.addLayer(this.inWARDSLayer);
        },
        addMiniSASSLayer: function () {
            let options = {
                url: '/bims_proxy/http://minisass.org:8080/geoserver/wms',
                params: {
                    name: 'MiniSASS',
                    layers: 'miniSASS:minisass_observations',
                    format: 'image/png',
                    getFeatureFormat: 'text/html'
                }
            };
            this.miniSASSLayer = new ol.layer.Tile({
                source: new ol.source.TileWMS(options)
            });
            this.miniSASSLayer.setVisible(false);
            this.map.addLayer(this.miniSASSLayer);
            Shared.Dispatcher.trigger(
                'layers:renderLegend',
                options['params']['layers'],
                options['params']['name'],
                options['url'],
                options['params']['layers'],
                false
            );
        },
        toggleMiniSASSLayer: function (e) {
            this.miniSASSSelected = $(e.target).is(":checked");
            if (this.miniSASSSelected) {
                this.miniSASSLayer.setVisible(true);
                // Move layer to top
                this.map.removeLayer(this.miniSASSLayer);
                this.map.getLayers().insertAt(this.map.getLayers().getLength(), this.miniSASSLayer);
                let mapLegend = $('#map-legend');
                mapLegend.find(`[data-name='${this.miniSASSLayer.getSource().getParams()['layers']}']`).show();
                if (!mapLegend.is('visible')) {
                    Shared.Dispatcher.trigger('map:showMapLegends');
                }
            } else {
                this.miniSASSLayer.setVisible(false);
                $('#map-legend').find(`[data-name='${this.miniSASSLayer.getSource().getParams()['layers']}']`).hide();
            }
        },
        toggleInward: function (e) {
            let self = this;
            this.inWARDSelected = $(e.target).is(":checked");

            if (this.inWARDSelected) {
                this.inWARDSLayer.setVisible(true);
                // Move layer to top
                this.map.removeLayer(this.inWARDSLayer);
                this.map.getLayers().insertAt(this.map.getLayers().getLength(), this.inWARDSLayer);

                // Show fetching message
                if (!this.fetchingInWARDSData) {
                    let fetchingMessage = $('<span class="fetching" style="font-size: 10pt; font-style: italic"> (fetching)</span>');
                    $(e.target).parent().find('.label').append(fetchingMessage);
                    $.ajax({
                        type: 'GET',
                        url: this.inWARDSStationsUrl,
                        success: function (data) {
                            let source = new ol.source.Vector({
                                features: (
                                    new ol.format.GeoJSON({featureProjection: 'EPSG:3857'})
                                ).readFeatures(data, {featureProjection: 'EPSG:3857'})
                            });
                            self.inWARDSLayer.setSource(source);
                            $(e.target).parent().find('.fetching').remove();
                        }
                    })
                    this.fetchingInWARDSData = true;
                }
            } else {
                self.inWARDSLayer.setVisible(false);
            }
        },
        showFeatureInfo: function (lon, lat, siteExist = false, featureData = null) {
            if (!this.miniSASSSelected && !this.inWARDSelected) {
                return false;
            }
            let self = this;
            lon = parseFloat(lon);
            lat = parseFloat(lat);
            const view = this.map.getView();
            const coordinate = ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857');
            let openSidePanel = false;

            if (this.inWARDSelected) {
                if (!featureData) {
                    return;
                }
                let properties = featureData.getProperties();
                let stationName = 'Station';
                if (properties.hasOwnProperty('station')) {
                    stationName = 'Station - ' + properties['station'];
                }
                let table = this.renderInwardsTable(properties);
                this.showContentToSidePanel(
                    lon, lat, stationName, table.prop('outerHTML'), siteExist, openSidePanel
                )
                openSidePanel = true;
            }

            if (this.miniSASSSelected) {
                const source = this.miniSASSLayer.getSource();
                const getFeatureFormat = source.getParams()['getFeatureFormat'];
                const layerName = source.getParams()['name'];
                const queryLayer = source.getParams()['layers'];
                let layerSource = source.getGetFeatureInfoUrl(
                    coordinate,
                    view.getResolution(),
                    view.getProjection(),
                    {'INFO_FORMAT': getFeatureFormat}
                );
                layerSource += '&QUERY_LAYERS=' + queryLayer;
                $.ajax({
                    type: 'POST',
                    url: '/get_feature/',
                    data: {
                        'layerSource': layerSource
                    },
                    success: function (data) {
                        if (!data) {
                            return true;
                        }
                        self.showContentToSidePanel(
                            lon, lat, layerName, data, siteExist, openSidePanel
                        )
                        openSidePanel = true;
                    }
                });
            }
        },
        showContentToSidePanel: function (lon, lat, panelTitle, panelContent, siteExist, openSidePanel = false) {
            if (!siteExist && !openSidePanel) {
                let marker = new ol.Feature({
                    geometry: new ol.geom.Point(
                        ol.proj.fromLonLat([lon, lat])
                    ),
                });
                Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
                Shared.Dispatcher.trigger('map:switchHighlight', [marker], true);
            }
            Shared.Dispatcher.trigger('sidePanel:addContentWithTab', panelTitle, panelContent);
        },
        renderInwardsTable: function (properties) {
            let $container = $(`<div></div>`);
            let table = $(`<table class="table table-striped"></table>`);
            $container.append(table);
            for (let key in properties) {
                if (properties[key] !== null && properties[key].constructor !== String && properties[key].constructor !== Number) {
                    continue;
                }
                let title = key;
                title = title.replace(/_/g, ' ');
                table.append(`<tr><td style="text-transform: capitalize; min-width: 100px;">${title}</td><td>${properties[key]}</td></tr>`);
            }
            let id = '';
            if (properties.hasOwnProperty('station')) {
                id = properties['station'];
            }
            $container.append(`<button class="btn btn-default" style="width: 100%" onclick="window.open('http://inwards.award.org.za/app_json/wq_csv.php?id=${id}')">Download csv</button>`);
            $container.append('<div style="text-align: right; font-size: 11pt">Data shared with permission from <a target="_blank" href="http://award.org.za/">http://award.org.za/</a></div>');
            return $container;
        },
        render: function () {
            this.$el.html(this.template());
            this.$el.hide();
            return this;
        },
        show: function () {
            this.$el.show();
            this.$el.find('.third-party-control-container').show();
            this.displayed = true;
        },
        hide: function () {
            this.$el.hide();
            this.$el.find('.third-party-control-container').hide();
            this.displayed = false;
        },
        isDisplayed: function () {
            return this.displayed;
        },
        closeClicked: function () {
            if (this.displayed) {
                Shared.Dispatcher.trigger('mapControlPanel:thirdPartyLayerClicked');
            }
        }
    })
});
