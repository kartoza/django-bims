
define([
    'backbone',
    'underscore',
    'shared',
    'models/location_site',
    'views/location_site',
    'views/map_control_panel',
    'openlayers'], function(Backbone, _, Shared, LocationSiteModel, LocationSiteView, MapControlPanelView, ol) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,
        locationSiteVectorSource: null,
        locationSiteViews: {},
        events: {
            'click .zoom-in': 'zoomInMap',
            'click .zoom-out': 'zoomOutMap',
            'click .layer-control': 'layerControlClicked'
        },
        initialize: function () {
            // Ensure methods keep the `this` references to the view itself
            _.bindAll(this, 'render');
            this.collection.fetch({
                success: this.render
            })
        },
        zoomInMap: function (e) {
            var view = this.map.getView();
            var zoom = view.getZoom();
            view.animate({
                zoom: zoom-1,
                duration: 250
            })
        },
        zoomOutMap: function (e) {
            var view = this.map.getView();
            var zoom = view.getZoom();
            view.animate({
                zoom: zoom+1,
                duration: 250
            })
        },
        mapClicked: function (e) {
            var self = this;
            var features = self.map.getFeaturesAtPixel(e.pixel);
            this.mapControlPanel.closeSearchPanel();
            if (features) {
                self.featureClicked(features[0]);
            } else {
               Shared.Dispatcher.trigger('sidePanel:closeSidePanel');
            }
        },
        featureClicked: function (feature) {
            var properties = feature.getProperties();
            if(this.locationSiteViews.hasOwnProperty(properties.id)) {
                var locationSiteView = this.locationSiteViews[properties.id];
                locationSiteView.clicked();
            }
        },
        layerControlClicked: function (e) {
        },
        renderCollection: function () {
            var self = this;

            for(var i=0; i < this.collection.length; i++) {
                var locationSiteModel = this.collection.models[i];
                var locationSiteView = new LocationSiteView({
                    model: locationSiteModel,
                    parent: this
                });
            }
        },
        render: function() {
            var self = this;

            this.$el.html(this.template());
            $('#map-container').append(this.$el);
            this.map = this.loadMap();

            self.renderCollection();

            this.map.on('click', function (e) {
               self.mapClicked(e);
            });

            this.mapControlPanel = new MapControlPanelView({
                parent: this
            });

            this.$el.append(this.mapControlPanel.render().$el);

            return this;
        },
        loadMap: function() {
            var baseSourceLayer;
            var self = this;

            if(bingMapKey) {
                baseSourceLayer = new ol.source.BingMaps({
                    key: bingMapKey,
                    imagerySet: 'AerialWithLabels'
                })
            } else {
                baseSourceLayer = new ol.source.OSM();
            }

            self.locationSiteVectorSource = new ol.source.Vector({});

            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                    anchor: [0.5, 46],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 0.75,
                    src: 'static/img/map-marker.png'
                }))
            });

            var styles = {
                'Point': iconStyle,
                'LineString': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'green',
                        width: 1
                    })
                }),
                'MultiPolygon': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'yellow',
                        width: 1
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 0, 0.1)'
                    })
                }),
                'Polygon': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'blue',
                        lineDash: [4],
                        width: 3
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(0, 0, 255, 0.1)'
                    })
                })
            };

            var styleFunction = function(feature) {
                return styles[feature.getGeometry().getType()];
            };

            var locationSiteVectorLayer = new ol.layer.Vector({
                source: self.locationSiteVectorSource,
                style: styleFunction
            });

            return new ol.Map({
                target: 'map',
                layers: [
                    new ol.layer.Tile({
                        source: baseSourceLayer
                    }),
                    locationSiteVectorLayer
                ],
                view: new ol.View({
                    center: ol.proj.fromLonLat([22.937506, -30.559482]),
                    zoom: 7
                }),
                controls: ol.control.defaults({
                    zoom: false
                })
            });
        },
        addLocationSiteFeatures: function (view, features) {
            this.locationSiteViews[view.id] = view;
            this.locationSiteVectorSource.addFeatures(features);
        }
    })
});
