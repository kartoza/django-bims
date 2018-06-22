define(['backbone', 'models/location_site', 'views/location_site'], function (Backbone, LocationSiteModel, LocationSiteView) {
    return Backbone.Collection.extend({
        model: LocationSiteModel,
        collectionAPI: "/api/location-site/?bbox=",
        url: "",
        viewCollection: [],
        updateUrl: function (bbox) {
            this.url = this.collectionAPI + bbox
        },
        renderCollection: function () {
            var self = this;
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];
            $.each(this.models, function (index, model) {
                self.viewCollection.push(new LocationSiteView({
                    model: model
                }));
            });
        }
    })
});
