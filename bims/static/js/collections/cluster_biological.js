define(['backbone', 'models/cluster_biological', 'views/cluster_biological', 'shared'], function (Backbone, ClusterModel, ClusterView, Shared) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: _.template(
            "/api/cluster/collection/records/?taxon=<%= taxon %>&search=<%= search %>" +
            "&icon_pixel_x=30&icon_pixel_y=30&zoom=<%= zoom %>&bbox=<%= bbox %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&date-from=<%= dateFrom %>&date-to=<%= dateTo %>" +
            ""),
        url: "",
        viewCollection: [],
        parameters: {
            taxon: '', zoom: 0, bbox: [],
            collector: '', category: '', dateFrom: '', dateTo: ''
        },
        initialize: function (initExtent) {
            this.initExtent = initExtent;
            Shared.Dispatcher.on('search:hit', this.updateParameters, this);
        },
        updateParameters: function (parameters) {
            var self = this;
            $.each(parameters, function (key, value) {
                self.parameters[key] = value;
            });
            this.parameters['taxon'] = null;
            this.toggleTaxonIndicator();
            this.getExtentOfRecords();
        },
        isActive: function () {
            // flag if this collection need to be called
            if (this.parameters['taxon'] || this.parameters['search']) {
                return true;
            } else {
                return false;
            }
        },
        getTaxon: function () {
            return this.parameters['taxon'];
        },
        toggleTaxonIndicator: function (taxonName) {
            if (this.parameters['taxon']) {
                $('#taxon-filter').html('Biodiversity filtered by : ' + taxonName);
                if ($('#taxon-filter').is(":hidden")) {
                    $('#taxon-filter').toggle("slide");
                }
            } else {
                if (!$('#taxon-filter').is(":hidden")) {
                    $('#taxon-filter').toggle("slide");
                }
            }
        },
        updateTaxon: function (taxon, taxonName) {
            this.parameters['taxon'] = taxon;
            this.parameters['search'] = null;
            this.toggleTaxonIndicator(taxonName);
            this.refresh();
        },
        updateZoomAndBBox: function (zoom, bbox) {
            this.parameters['zoom'] = zoom;
            this.parameters['bbox'] = bbox;
            this.refresh();
        },
        getExtentOfRecords: function () {
            var self = this;
            // get extent for all record and fit it to map
            this.parameters['date-from'] = this.parameters['dateFrom'];
            this.parameters['date-to'] = this.parameters['dateTo'];
            $.ajax({
                url: '/api/cluster/collection/records/extent/',
                data: this.parameters,
                dataType: "json",
                success: function (data) {
                    if (data.length == 4) {
                        Shared.Dispatcher.trigger('map:zoomToExtent', data);
                    } else {
                        Shared.Dispatcher.trigger('map:zoomToExtent', self.initExtent);
                    }
                }
            });
        },
        refresh: function () {
            if (this.parameters['zoom'] &&
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
