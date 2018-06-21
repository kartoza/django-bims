define(['backbone', 'models/cluster_biological', 'views/cluster_biological', 'shared'], function (Backbone, ClusterModel, ClusterView, Shared) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: _.template("/api/cluster/collection/taxon/<%= taxonID %>/?icon_pixel_x=30&icon_pixel_y=30&zoom=<%= zoom %>&bbox=<%= bbox %>"),
        url: "",
        viewCollection: [],
        initialize: function (options) {
            Shared.Dispatcher.on('searchResult:clicked', this.updateTaxon, this);
        },
        updateTaxon: function (taxonID) {
            this.taxonID = taxonID;
            this.refresh();
        },
        updateZoomAndBBox: function (zoom, bbox) {
            this.zoom = zoom;
            this.bbox = bbox;
            this.refresh();
        },
        refresh: function () {
            if (this.taxonID && this.zoom && this.bbox) {
                this.url = this.clusterAPI(
                    {
                        taxonID: this.taxonID,
                        zoom: this.zoom,
                        bbox: this.bbox
                    }
                );
            }
        },
        renderCollection: function () {
            var self = this;
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];
            $.each(this.models, function (index, model) {
                self.viewCollection.push(new ClusterView({
                    model: model
                }));
            });
        }
    })
});
