define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery', 'ol'], function (Shared, Backbone, _, jqueryUi, $, ol) {
    return Backbone.View.extend({
        template: _.template($('#third-party-layer-panel-template').html()),
        isEmpty: true,
        layer: null,
        source: null,
        displayed: false,
        miniSASSSelected: false,
        events: {
            'click .close-button': 'closeClicked',
            'click .update-search': 'updateSearch',
            'change .mini-sass-check': 'toggleMiniSASSLayer'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.map = options.map;
            this.addMiniSASSLayer();
            Shared.Dispatcher.on('third_party_layers:showFeatureInfo', this.showFeatureInfo, this);
            // this.createPolygonInteraction();
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
        showFeatureInfo: function (lon, lat, siteExist = false) {
            if (!this.miniSASSSelected) {
                return false;
            }
            console.log('showFeatureInfo');
            lon = parseFloat(lon);
            lat = parseFloat(lat);
            const view = this.map.getView();
            const coordinate = ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857');
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
                    if (!siteExist) {
                        let marker = new ol.Feature({
                            geometry: new ol.geom.Point(
                                ol.proj.fromLonLat([lon, lat])
                            ),
                        });
                        Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
                        Shared.Dispatcher.trigger('map:switchHighlight', [marker], true);
                    }
                    Shared.Dispatcher.trigger('sidePanel:addContentWithTab', layerName, data);
                }
            });
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
