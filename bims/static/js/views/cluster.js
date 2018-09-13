define(['backbone', 'models/cluster', 'ol', 'shared', 'jquery'], function (Backbone, Cluster, ol, Shared, $) {
    return Backbone.View.extend({
        initialize: function (options) {
            this.render();
        },
        render: function () {
            var modelJson = this.model.toJSON();
            var geometry = modelJson['point'];
            delete modelJson['geometry'];
            modelJson['text'] = modelJson['name'];

            // assign count
            var count = modelJson['count'];
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
            Shared.Dispatcher.trigger('map:addBiodiversityFeatures', this.features)
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
