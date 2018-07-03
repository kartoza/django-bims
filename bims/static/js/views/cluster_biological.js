define(['backbone', 'models/cluster_biological', 'ol', 'shared'], function (Backbone, Cluster, ol, Shared) {
    return Backbone.View.extend({
        initialize: function (options) {
            this.render();
        },
        clicked: function () {
            var coord = ol.proj.transform(
                this.model.attributes['geometry']['coordinates'],
                "EPSG:4326", "EPSG:3857");
            var properties = this.model.attributes['properties'];
            var template = _.template($('#record-detail-template').html());
            Shared.Dispatcher.trigger('map:showPopup', coord, template(properties));
        },
        render: function () {
            var modelJson = this.model.toJSON();
            var properties = this.model.attributes['properties'];
            this.id = this.model.attributes['properties']['id'];
            if (!this.model.attributes['properties']['count']) {
                Shared.Dispatcher.on('cluster-biology' + this.id + ':clicked', this.clicked, this);
            }
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
