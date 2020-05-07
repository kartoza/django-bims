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
        inWARDSStationsUrl: 'http://inwards.award.org.za/app_json/stations.php?wma=%27inkomati_usuthu%27,%27limpopo%27,%27olifants_letaba%27',
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
                self.inWARDSLayer.setVisible(true);
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
            lon = parseFloat(lon);
            lat = parseFloat(lat);
            const view = this.map.getView();
            const coordinate = ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857');

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
                        this.showContentToSidePanel(
                            lon, lat, layerName, data, siteExist
                        )
                    }
                });
            } else {
                let table = this.renderInwardsTable(featureData.getProperties());
                this.showContentToSidePanel(
                    lon, lat, 'Station', table.prop('outerHTML'), siteExist
                )
            }
        },
        showContentToSidePanel: function (lon, lat, panelTitle, panelContent, siteExist) {
            if (!siteExist) {
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
            let table = $(`<table class="table table-striped"></table>`);
            for (let key in properties) {
                if (properties[key] !== null && properties[key].constructor !== String && properties[key].constructor !== Number) {
                    continue;
                }
                let title = key;
                title = title.replace(/_/g, ' ');
                table.append(`<tr><td style="text-transform: capitalize; min-width: 100px;">${title}</td><td>${properties[key]}</td></tr>`);
            }
            return table;
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
