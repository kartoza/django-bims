define(['backbone', 'models/location_site', 'views/location_site', 'shared'], function (Backbone, LocationSiteModel, LocationSiteView, Shared) {
    return Backbone.Collection.extend({
        model: LocationSiteModel,
        baseAPI: "/api/location-site/",
        collectionAPI: _.template("/api/location-site/cluster/?icon_pixel_x=<%= clusterSize %>&icon_pixel_y=<%= clusterSize %>&zoom=<%= zoom %>&bbox=<%= bbox %>"),
        url: "",
        viewCollection: [],
        updateUrl: function (bbox, zoom) {
            this.url = this.collectionAPI({
                bbox: bbox,
                zoom: zoom,
                clusterSize: Shared.ClusterSize
            });
        },
        renderCollection: function () {
            var self = this;
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];
            $.each(this.models, function (index, model) {
                model.url = self.baseAPI + model.get('id')
                self.viewCollection.push(new LocationSiteView({
                    model: model
                }));
            });
        }
    })
});
