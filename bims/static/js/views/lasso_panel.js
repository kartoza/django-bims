define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery', 'ol'], function (Shared, Backbone, _, jqueryUi, $, ol) {
    return Backbone.View.extend({
        template: _.template($('#lasso-control-panel-template').html()),
        isEmpty: true,
        layer: null,
        source: null,
        polygonDraw: null,
        polygonCoordinates: null,
        displayed: false,
        polygonExist: false,
        events: {
            'click .polygonal-lasso-tool': 'drawPolygon',
            'click .clear-lasso': 'clearLasso',
            'click .update-search': 'updateSearch'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.map = options.map;
            this.createPolygonInteraction();
        },
        createPolygonInteraction: function () {
            let self = this;
            this.source = new ol.source.Vector({wrapX: false});
            this.layer = new ol.layer.Vector({
                source: self.source
            });
            this.polygonDraw = new ol.interaction.Draw({
                source: self.source,
                type: 'Polygon'
            });
            this.polygonDraw.on('drawend', function (evt) {
                // Zoom to extent
                let polygonExtent = evt.feature.getGeometry().getExtent();
                let transformedCoordinates = [];
                let coordinates = evt.feature.getGeometry().getCoordinates()[0];
                for (let i=0; i<coordinates.length; i++) {
                    let newCoord = ol.proj.transform(coordinates[i], ol.proj.get('EPSG:3857'), ol.proj.get('EPSG:4326'));
                    transformedCoordinates.push(newCoord);
                }
                self.polygonCoordinates = transformedCoordinates;
                self.polygonExist = true;
                self.$el.find('.update-search').removeClass('disabled');
                self.$el.find('.clear-lasso').removeClass('disabled');
                Shared.Dispatcher.trigger('map:zoomToExtent', polygonExtent, false, false);
                Shared.Dispatcher.trigger('map:setPolygonDrawn', polygonExtent);
            });
            this.polygonDraw.on('drawstart', function () {
                self.source.clear();
            });
        },
        render: function () {
            this.$el.html(this.template());
            this.$el.hide();
            return this;
        },
        getPolygonCoordinates: function () {
            if (this.polygonCoordinates) {
                return JSON.stringify(this.polygonCoordinates);
            }
            return '';
        },
        show: function () {
            this.$el.show();
            this.$el.find('.lasso-control-container').show();
            if (this.polygonExist) {
                this.$el.find('.update-search').removeClass('disabled');
                this.$el.find('.clear-lasso').removeClass('disabled');
            } else {
                if (!Shared.CurrentState.SEARCH) {
                    this.$el.find('.update-search').addClass('disabled');
                }
                this.$el.find('.clear-lasso').addClass('disabled');
            }
            this.displayed = true;
        },
        hide: function () {
            this.$el.hide();
            this.$el.find('.lasso-control-container').hide();
            this.stopDrawing();
            this.displayed = false;
        },
        isDisplayed: function () {
            return this.displayed;
        },
        drawPolygon: function () {
            this.$el.find('.polygonal-lasso-tool').addClass('selected');
            this.map.removeLayer(this.layer);
            this.map.addLayer(this.layer);
            this.map.addInteraction(this.polygonDraw);
            Shared.Dispatcher.trigger('map:toggleMapInteraction', true);
        },
        stopDrawing: function () {
            this.$el.find('.polygonal-lasso-tool').removeClass('selected');
            this.map.removeInteraction(this.polygonDraw);
            Shared.Dispatcher.trigger('map:toggleMapInteraction', false);
        },
        clearLasso: function (evt) {
            if (evt) {
                let div = $(evt.target);
                if (div.hasClass('disabled')) {
                    return;
                }
            }
            this.map.removeLayer(this.layer);
            this.source.clear();
            this.polygonCoordinates = null;
            this.polygonExist = false;
            if (!Shared.CurrentState.SEARCH) {
                this.$el.find('.update-search').addClass('disabled');
            }
            this.$el.find('.clear-lasso').addClass('disabled');
            this.stopDrawing();
            Shared.Dispatcher.trigger('map:setPolygonDrawn', null);
        },
        drawPolygonFromJSON: function (jsonCoordinates) {
            if (this.polygonExist) {
                return;
            }
            this.polygonCoordinates = JSON.parse(jsonCoordinates);
            let polyCoords = [];
            for (let i in this.polygonCoordinates) {
                let c = this.polygonCoordinates[i];
                polyCoords.push(ol.proj.transform(c, 'EPSG:4326', 'EPSG:3857'));
            }
            const feature = new ol.Feature({
                geometry: new ol.geom.Polygon([polyCoords])
            });
            this.map.removeLayer(this.layer);
            this.map.addLayer(this.layer);
            this.source.addFeature(feature);
            this.polygonExist = true;
        },
        updateSearch: function (evt) {
            let div = $(evt.target);
            if (div.hasClass('disabled')) {
                return;
            }
            Shared.Dispatcher.trigger('search:doSearch');
        }
    })
});
