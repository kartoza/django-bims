define(['backbone', 'models/location_site', 'ol', 'shared'], function (Backbone, LocationSite, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        initialize: function (options) {
            this.render();
        },
        clicked: function () {
            var self = this;
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', self.model.toJSON());
            if (Shared.LocationSiteDetailXHRRequest) {
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

            Shared.Dispatcher.on('locationSite-' + this.id + ':clicked', this.clicked, this);
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

            this.features = new ol.format.GeoJSON().readFeatures(geojson, {
                featureProjection: 'EPSG:3857'
            });
            Shared.Dispatcher.trigger('map:addBiodiversityFeatures', this.features)
        },
        destroy: function () {
            Shared.Dispatcher.unbind('locationSite-' + this.id + ':clicked');
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
