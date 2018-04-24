define(['backbone', 'models/location_site', 'openlayers', 'shared'], function (Backbone, LocationSite, ol, Shared) {
   return Backbone.View.extend({
        id: 0,
        initialize: function (options) {
            this.parent = options.parent;
            this.render();
        },
        clicked: function() {
            var self = this;
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', self.model.toJSON());
            if(Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }
            Shared.LocationSiteDetailXHRRequest = self.model.fetch({
                success: function (data) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelDetail', self.model.toJSON());
                    Shared.LocationSiteDetailXHRRequest = null;
                }
            });
        },
        render: function () {
            var modelJson = this.model.toJSON();
            this.id = modelJson['id'];
            var geometry = JSON.parse(modelJson['geometry']);
            delete modelJson['geometry'];
            var geojson = {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': geometry,
                        'properties': modelJson
                    }
                ]
            };

            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                    anchor: [0.5, 46],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 0.75,
                    src: 'static/img/marker.png'
                }))
            });

            var features = new ol.format.GeoJSON().readFeatures(geojson, {
                featureProjection: 'EPSG:3857'
            });

            this.parent.addLocationSiteFeatures(this, features);
        }
   })
});
