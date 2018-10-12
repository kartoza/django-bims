define(['backbone', 'models/cluster_biological', 'ol', 'shared'], function (Backbone, Cluster, ol, Shared) {
    return Backbone.View.extend({
        initialize: function (options) {
            this.render();
        },
        clicked: function () {
            var properties = this.model.attributes['properties'];
            if (properties['taxon_gbif_id']) {
                Shared.Dispatcher.trigger(
                    'taxonDetail:show',
                    properties.taxon_gbif_id,
                    properties.taxonomy.species
                );
            }
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
            Shared.Dispatcher.trigger('map:addBiodiversityFeatures', this.features, true)
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
