define(['backbone', 'models/cluster_biological', 'views/cluster_biological', 'shared'], function (Backbone, ClusterModel, ClusterView, Shared) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: _.template(
            "/api/cluster/collection/taxon/<%= taxonID %>/?" +
            "icon_pixel_x=30&icon_pixel_y=30&zoom=<%= zoom %>&bbox=<%= bbox %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&date-from=<%= dateFrom %>&date-to=<%= dateTo %>" +
            ""),
        url: "",
        viewCollection: [],
        parameters: {},
        initialize: function () {
            Shared.Dispatcher.on('search:hit', this.updateParameters, this);
        },
        updateParameters: function (parameters) {
            this.parameters = parameters;
            this.parameters['taxonID'] = null;
        },
        getTaxon: function () {
            return this.parameters['taxonID'];
        },
        updateTaxon: function (taxonID) {
            this.parameters['taxonID'] = taxonID;
            this.refresh();
        },
        updateZoomAndBBox: function (zoom, bbox) {
            this.parameters['zoom'] = zoom;
            this.parameters['bbox'] = bbox;
            this.refresh();
        },
        getExtentOfRecords: function () {
            // get extent for all record and fit it to map
            this.parameters['date-from'] = this.parameters['dateFrom'];
            this.parameters['date-to'] = this.parameters['dateTo'];
            $.ajax({
                url: '/api/cluster/collection/taxon/' + this.getTaxon() + '/extent/',
                data: this.parameters,
                dataType: "json",
                success: function (data) {
                    if (data.length == 4) {
                        Shared.Dispatcher.trigger('map:zoomToExtent', data);
                    }
                }
            });
        },
        refresh: function () {
            if (this.parameters['taxonID'] &&
                this.parameters['zoom'] &&
                this.parameters['bbox']) {
                this.url = this.clusterAPI(this.parameters);
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
