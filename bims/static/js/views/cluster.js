define(['backbone', 'models/cluster', 'ol', 'shared'], function (Backbone, Cluster, ol, Shared) {
    return Backbone.View.extend({
        initialize: function (options) {
            this.render();
        },
        clicked: function () {
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', this.model.toJSON());
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelDetail', this.model.toJSON()['cluster_data']);
        },
        render: function () {
            var modelJson = this.model.toJSON();
            this.id = modelJson['id'];
            Shared.Dispatcher.on('locationSite-' + this.id + ':clicked', this.clicked, this);

            var geometry = modelJson['point'];
            delete modelJson['geometry'];
            modelJson['text'] = modelJson['name'];
            var geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": geometry
                },
                "properties": modelJson
            };

            this.features = new ol.format.GeoJSON().readFeatures(geojson, {
                featureProjection: 'EPSG:3857'
            });
            Shared.Dispatcher.trigger('map:addLocationSiteFeatures', this.features)
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
