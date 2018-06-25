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

            // assign count
            var count = 0;
            try {
                count = modelJson['cluster_data']['location site']['details']['records'];
            }
            catch (err) {
            }

            if (count === 0) {
                return
            }

            modelJson['count'] = count;
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
            Shared.Dispatcher.trigger('map:addClusterFeatures', this.features)
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
