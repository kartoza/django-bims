define([
    'backbone',
    'models/cluster_location_site',
    'views/cluster_location_site',
    'shared',
    'ol', 'jquery'], function (Backbone, ClusterModel, ClusterView, Shared, ol, $) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        apiParameters: _.template("?taxon=<%= taxon %>&search=<%= search %>&siteId=<%= siteId %>" +
            "&icon_pixel_x=<%= clusterSize %>&icon_pixel_y=<%= clusterSize %>&zoom=<%= zoom %>&bbox=<%= bbox %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&yearFrom=<%= yearFrom %>&yearTo=<%= yearTo %>&months=<%= months %>&boundary=<%= boundary %>&userBoundary=<%= userBoundary %>" +
            "&referenceCategory=<%= referenceCategory %>&reference=<%= reference %>&endemic=<%= endemic %>"),
        clusterAPI: "/api/collection/cluster/",
        url: "",
        viewCollection: [],
        status: "",
        initialSearch: true,
        secondSearch: false,
        fromSearchClick: false,
        fetchXhr: null,
        clusterData: null,
        defaultZoom: 8,
        filteredByTaxon: true,
        parameters: {
            taxon: '', zoom: 0, bbox: [], siteId: '',
            collector: '', category: '', yearFrom: '', yearTo: '', months: '',
            boundary: '', userBoundary: '', referenceCategory: '', reference: '', endemic: '',
            clusterSize: Shared.ClusterSize
        },
        initialize: function (initExtent) {
            this.initExtent = initExtent;
            Shared.Dispatcher.on('clusterBiological:clearClusters', this.clearClusters, this);
            Shared.Dispatcher.on(Shared.EVENTS.CLUSTER.GET, this.getClusters, this);
            Shared.Dispatcher.on('clusterBiological:resetParameters', this.clearParameters, this);
            Shared.Dispatcher.on('clusterBiological:clearFilterByTaxon', this.clearFilterByTaxon, this);
        },
        clearParameters: function () {
            this.parameters['taxon'] = '';
            this.parameters['siteId'] = '';
            this.parameters['search'] = '';
            this.parameters['collector'] = '';
            this.parameters['category'] = '';
            this.parameters['yearFrom'] = '';
            this.parameters['yearTo'] = '';
            this.parameters['userBoundary'] = '';
            this.parameters['referenceCategory'] = '';
            this.parameters['boundary'] = '';
            this.parameters['reference'] = '';
            this.parameters['endemic'] = '';
            Shared.Dispatcher.trigger('cluster:updated', this.parameters);
            if (typeof filterParameters !== 'undefined') {
                filterParameters = $.extend(true, {}, this.parameters);
            }
        },
        resetClusters: function () {
            this.clusterData = [];
            this.fromSearchClick = false;
            if (this.fetchXhr) {
                this.fetchXhr.abort();
                this.initialSearch = true;
                this.secondSearch = false;
            }
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
        },
        clearClusters: function () {
            this.clearParameters();
            this.resetClusters();
            this.toggleTaxonIndicator();
        },
        getClusters: function (parameters) {
            this.resetClusters();
            this.fromSearchClick = true;
            parameters['bbox'] = null;
            parameters['zoom'] = this.defaultZoom;
            this.updateParameters(parameters);
        },
        updateParameters: function (parameters) {
            var self = this;
            $.each(parameters, function (key, value) {
                self.parameters[key] = value;
            });
            Shared.Dispatcher.trigger('cluster:updated', this.parameters);
            if (typeof filterParameters !== 'undefined') {
                filterParameters = $.extend(true, {}, this.parameters);
            }
            this.parameters['taxon'] = null;
            this.toggleTaxonIndicator();
            if (this.isActive()) {
                this.fetchXhr = this.fetchCluster();
            }
        },
        fetchCluster: function (zoomToExtent) {
            var self = this;
            this.parameters['bbox'] = null;
            this.url = this.clusterAPI + this.apiParameters(this.parameters);
            return this.fetch({
                success: function () {
                },
                complete: function () {
                    var timeout = 3000;
                    if (self.initialSearch) {
                        timeout = 500;
                        self.initialSearch = false;
                        self.secondSearch = true;
                        if (self.fromSearchClick) {
                            Shared.Dispatcher.trigger('map:zoomToDefault');
                        }
                        Shared.Dispatcher.trigger('map:startFetching');
                    }
                    if (self.secondSearch) {
                        timeout = 1000;
                        self.secondSearch = true;
                    }
                    if(self.status === 'processing') {
                        self.renderCollection();
                        setTimeout(function () {
                            self.fetchCluster(zoomToExtent)
                        }, timeout);
                    } else {
                        self.initialSearch = true;
                        self.secondSearch = false;
                        if(self.fromSearchClick || zoomToExtent) {
                            self.createExtents();
                            self.fromSearchClick = false;
                        }
                        Shared.Dispatcher.trigger('map:finishFetching');
                        self.renderCollection();
                    }
                }
            })
        },
        isActive: function () {
            // flag if this collection need to be called
            if (!this.parameters['taxon']
                && !this.parameters['search']
                && !this.parameters['siteId']
                && !this.parameters['collector']
                && !this.parameters['category']
                && !this.parameters['yearFrom']
                && !this.parameters['yearTo']
                && !this.parameters['userBoundary']
                && !this.parameters['referenceCategory']
                && !this.parameters['reference']
                && !this.parameters['endemic']
                && !this.parameters['boundary']) {
                return false
            } else {
                return true;
            }
        },
        getTaxon: function () {
            return this.parameters['taxon'];
        },
        parse: function (response) {
            if (response.hasOwnProperty('data')) {
                this.clusterData = response['data'];
            }
            if (response.hasOwnProperty('status')) {
                if(response['status'].hasOwnProperty('current_status')) {
                    this.status = response['status']['current_status'];
                } else {
                    this.status = response['status'];
                }
            }
        },
        toggleTaxonIndicator: function (taxonName) {
            var self = this;
            var $taxonFilter = $('#taxon-filter');
            if (this.parameters['taxon']) {
                self.filteredByTaxon = true;
                $taxonFilter.html('Sites filtered by : ' + taxonName +
                    ' <i class="fa fa-times" style="color: red"></i> ');
                $('#taxon-filter .fa-times').click(function () {
                    Shared.Dispatcher.trigger('sidePanel:closeSidePanel');
                    self.parameters['taxon'] = null;
                    self.toggleTaxonIndicator('');
                    self.refetchClusters(true);
                    self.filteredByTaxon = false;
                });
                if ($taxonFilter.is(":hidden")) {
                    $taxonFilter.toggle("slide");
                }
            } else {
                self.filteredByTaxon = false;
                if (!$taxonFilter.is(":hidden")) {
                    $taxonFilter.toggle("slide");
                }
            }
        },
        clearFilterByTaxon: function () {
            if (!this.filteredByTaxon) {
                return false;
            }
            this.parameters['taxon'] = null;
            this.toggleTaxonIndicator('');
            this.refetchClusters();
            this.filteredByTaxon = false;
        },
        filterClustersByTaxon: function (taxon, taxonName) {
            this.parameters['taxon'] = taxon;
            this.toggleTaxonIndicator(taxonName);
            this.refresh();
        },
        updateZoomAndBBox: function (zoom, bbox) {
            this.parameters['zoom'] = zoom;
            this.parameters['bbox'] = bbox.join(',');
            this.refresh();
        },
        createExtents: function (pastCoordinates) {
            var coordinates = [];
            if (!this.clusterData) {
                return false;
            }
            $.each(this.clusterData, function (index, cluster) {
                var locationCoordinates = cluster['o'].split(',');
                var lon = parseFloat(locationCoordinates[0]);
                var lat = parseFloat(locationCoordinates[1]);
                coordinates.push([lon, lat]);
            });
            if (pastCoordinates) {
                coordinates.push.apply(coordinates, pastCoordinates);
            }
            if (coordinates.length > 0) {
                var ext = ol.extent.boundingExtent(coordinates);
                Shared.Dispatcher.trigger('map:zoomToExtent', ext);
            }
        },
        refetchClusters: function (zoomToExtent) {
            Shared.Dispatcher.trigger('cluster:updated', this.parameters);
            var self = this;
            if (this.isActive()) {
                this.resetClusters();
                this.fetchXhr = this.fetchCluster(zoomToExtent);
            } else {
                Shared.Dispatcher.trigger('map:zoomToExtent', self.initExtent);
            }
        },
        getExtentOfRecords: function () {
            Shared.Dispatcher.trigger('cluster:updated', this.parameters);
            var self = this;
            if (this.isActive()) {
                var extentUrl = '/api/collection/extent/' + this.apiParameters(this.parameters);
                $.ajax({
                    url: extentUrl,
                    dataType: "json",
                    success: function (data) {
                        if (data.length === 4) {
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
                this.parameters['bbox'] &&
                !this.fromSearchClick) {
                this.url = this.clusterAPI + this.apiParameters(this.parameters);
            }
        },
        renderCollection: function () {
            var self = this;
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];
            $.each(this.clusterData, function (index, cluster) {
                var clusterModel = new ClusterModel({
                    id: cluster['id'],
                    name: cluster['n'],
                    coordinates: cluster['o']
                });
                self.viewCollection.push(new ClusterView({
                    model: clusterModel
                }));
            });
        }
    })
});
