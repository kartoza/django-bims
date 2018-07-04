define(['backbone', 'models/location_site', 'ol', 'shared'], function (Backbone, LocationSite, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        initialize: function (options) {
            this.render();
        },
        clicked: function () {
            var self = this;
            var properties = this.model.attributes['properties'];
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', properties);
            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }
            Shared.LocationSiteDetailXHRRequest = $.get({
                url: this.model.url,
                dataType: 'json',
                success: function (data) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelDetail', data);
                    Shared.LocationSiteDetailXHRRequest = null;
                },
                error: function (req, err) {
                    self.loadSuccess();
                }
            });
        },
        render: function () {
            var modelJson = this.model.toJSON();
            var properties = this.model.attributes['properties'];
            this.id = this.model.attributes['properties']['id'];
            this.model.set('id', this.id)
            if (!this.model.attributes['properties']['count']) {
                Shared.Dispatcher.on('locationSite-' + this.id + ':clicked', this.clicked, this);
            }
            this.features = new ol.format.GeoJSON().readFeatures(modelJson, {
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
