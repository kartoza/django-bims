define(['backbone', 'models/cluster_biological', 'ol', 'shared'], function (Backbone, Cluster, ol, Shared) {
    return Backbone.View.extend({
        initialize: function (options) {
            this.render();
        },
        render: function () {
            var modelJson = this.model.toJSON();
            this.id = modelJson['id'];
            this.features = new ol.format.GeoJSON().readFeatures(modelJson, {
                featureProjection: 'EPSG:3857'
            });
            Shared.Dispatcher.trigger('map:addClusterFeatures', this.features, true)
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
