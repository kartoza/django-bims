define(['backbone', 'models/location_site', 'ol', 'shared'], function (Backbone, LocationSite, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        initialize: function (options) {
            this.render();
        },
        clicked: function () {
            Shared.Dispatcher.trigger(
                'siteDetail:show', this.id, this.name);
        },
        render: function () {
            var self = this;
            this.id = this.model.getId();
            this.name = this.model.get('name');
            this.model.set('id', this.id);
            Shared.Dispatcher.on('locationSite-' + this.id + ':clicked', this.clicked, this);
            this.feature = new ol.Feature({
                geometry: new ol.geom.Point(
                    ol.proj.fromLonLat(self.model.getCoordinates())
                ),
                id: this.id,
                name: this.name,
                record_type: 'cluster-site'
            });
            this.features = [];
            this.features.push(this.feature);
            Shared.Dispatcher.trigger('map:addLocationSiteClusterFeatures', this.features);
        },
        destroy: function () {
            Shared.Dispatcher.unbind('locationSite-' + this.id + ':clicked');
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
