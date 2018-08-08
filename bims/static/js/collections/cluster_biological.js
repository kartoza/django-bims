define(['backbone', 'models/cluster_biological', 'views/cluster_biological', 'shared'], function (Backbone, ClusterModel, ClusterView, Shared) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: _.template(
            "/api/collection/cluster/?taxon=<%= taxon %>&search=<%= search %>" +
            "&icon_pixel_x=30&icon_pixel_y=30&zoom=<%= zoom %>&bbox=<%= bbox %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&yearFrom=<%= yearFrom %>&yearTo=<%= yearTo %>&months=<%= months %>" +
            ""),
        url: "",
        viewCollection: [],
        parameters: {
            taxon: '', zoom: 0, bbox: [],
            collector: '', category: '', yearFrom: '', yearTo: '', months: ''
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
            if (!this.parameters['taxon']
                && !this.parameters['search']
                && !this.parameters['collector']
                && !this.parameters['category']
                && !this.parameters['yearFrom']
                && !this.parameters['yearTo']) {
                return false
            } else {
                return true;
            }
        },
        getTaxon: function () {
            return this.parameters['taxon'];
        },
        toggleTaxonIndicator: function (taxonName) {
            var self = this;
            if (this.parameters['taxon']) {
                $('#taxon-filter').html('Biodiversity filtered by : ' + taxonName +
                    ' <i class="fa fa-times" style="color: red"></i> ');
                $('#taxon-filter .fa-times').click(function () {
                    self.parameters['taxon'] = null;
                    self.toggleTaxonIndicator('');
                    Shared.Dispatcher.trigger('map:reloadXHR');
                });
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
            this.parameters['bbox'] = bbox.join(',');
            this.refresh();
        },
        getExtentOfRecords: function () {
            Shared.Dispatcher.trigger('cluster:updated', this.parameters);
            var self = this;
            if (this.isActive()) {
                $.ajax({
                    url: '/api/collection/extent/',
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
            } else {
                Shared.Dispatcher.trigger('map:zoomToExtent', self.initExtent);
            }
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
