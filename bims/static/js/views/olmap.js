
define([
    'backbone',
    'underscore',
    'shared',
    'models/location_site',
    'views/location_site',
    'views/map_control_panel',
    'openlayers',
    'jquery'], function(Backbone, _, Shared, LocationSiteModel, LocationSiteView, MapControlPanelView, ol, $) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,
        locationSiteVectorSource: null,
        geocontextOverlay: null,
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
            });
        },
        zoomInMap: function (e) {
            let view = this.map.getView();
            let zoom = view.getZoom();
            view.animate({
                zoom: zoom-1,
                duration: 250
            })
        },
        zoomOutMap: function (e) {
            let view = this.map.getView();
            let zoom = view.getZoom();
            view.animate({
                zoom: zoom+1,
                duration: 250
            })
        },
        mapClicked: function (e) {
            let self = this;
            let features = self.map.getFeaturesAtPixel(e.pixel);

            if (features) {
                self.featureClicked(features[0]);
            } else {
               Shared.Dispatcher.trigger('sidePanel:closeSidePanel');
            }

            // Close opened control panel
            this.mapControlPanel.closeAllPanel();

            if(this.mapControlPanel.locationControlActive) {
                this.showGeoContext(e.coordinate);
            }
        },
        showGeoContext: function (coordinate) {

            if(!geocontextUrl) {
                return false;
            }

            let lonlat = ol.proj.transform(coordinate, "EPSG:3857", "EPSG:4326");

            // Show popup
            let hdms = ol.coordinate.toStringHDMS(ol.proj.transform(
                coordinate, "EPSG:3857", "EPSG:4326"
            ));

            this.geoOverlayContent.innerHTML = '<div class=small-loading></div>';
            this.geocontextOverlay.setPosition(coordinate);
            let lon = lonlat[0];
            let lan = lonlat[1];
            let self = this;

            let url = geocontextUrl + "/geocontext/value/list/"+lon+"/"+lan+"/?with-geometry=False";

            $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    self.geoOverlayContent.innerHTML = JSON.stringify(data);
                },
                error: function(req, err){ console.log(err); }
            });
        },
        featureClicked: function (feature) {
            let properties = feature.getProperties();
            if(this.locationSiteViews.hasOwnProperty(properties.id)) {
                let locationSiteView = this.locationSiteViews[properties.id];
                locationSiteView.clicked();
            }
        },
        layerControlClicked: function (e) {
        },
        renderCollection: function () {
            var self = this;

            for(let i=0; i < this.collection.length; i++) {
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

            this.geoOverlayContainer = document.getElementById('geocontext-popup');
            this.geoOverlayContent = document.getElementById('geocontext-content');
            this.geoOverlayCloser = document.getElementById('geocontext-closer');

            this.geocontextOverlay = new ol.Overlay({
                element: this.geoOverlayContainer,
                autoPan: true,
                autoPanAnimation: {
                    duration: 250
                }
            });

            this.geoOverlayCloser.onclick = function () {
                self.geocontextOverlay.setPosition(undefined);
                self.geoOverlayCloser.blur();
                return false;
            };

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
                }),
                overlays: [this.geocontextOverlay]
            });
        },
        addLocationSiteFeatures: function (view, features) {
            this.locationSiteViews[view.id] = view;
            this.locationSiteVectorSource.addFeatures(features);
        }
    })
});
