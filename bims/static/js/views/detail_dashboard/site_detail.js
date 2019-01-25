define([
    'backbone',
    'underscore',
    'ol',
    'jquery',
    'shared',
    'htmlToCanvas'
], function (
    Backbone,
    _,
    ol,
    $,
    Shared,
    HtmlToCanvas
) {
    return Backbone.View.extend({
        id: 'detailed-site-dashboard',
        isOpen: false,
        template: _.template($('#detailed-site-dashboard').html()),
        dummyPieData: [25, 2, 7, 10, 12, 25, 60],
        objectDataByYear: 'object_data_by_year',
        yearsArray: 'years_array',
        dummyPieColors: ['#2d2d2d', '#565656', '#6d6d6d', '#939393', '#adadad', '#bfbfbf', '#d3d3d3'],
        fetchBaseUrl: '/api/location-sites-summary/?',
        fetchLocationSiteCoordinateUrl: '/api/location-sites-coordinate/?',
        csvDownloadUrl: '/api/collection/download/',
        locationSiteCoordinateRequestXHR: null,
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        uniqueSites: [],
        occurrenceData: {},
        vectorLayerFromMainMap: null,
        siteLayerSource: null,
        siteLayerVector: null,
        categoryColor: {
            'Native': '#a13447',
            'Non-Native': '#00a99d',
            'Translocated': '#e0d43f'
        },
        pieOptions: {
            legend: {
                display: true
            },
            cutoutPercentage: 0,
            maintainAspectRatio: true,
        },
        categories: {
            'indigenous': 'Native',
            'alien': 'Non-Native',
            'translocated': 'Translocated'
        },
        events: {
            'click .close-dashboard': 'closeDashboard',
            'click #export-locationsite-map': 'exportLocationsiteMap',
            'click .download-origin-chart': 'downloadOriginChart',
            'click .download-record-timeline': 'downloadRecordTimeline',
            'click .download-collection-timeline': 'downloadCollectionTimeline',
            'click .download-as-csv': 'downloadAsCSV'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.$el.hide();
            this.mapLocationSite = null;
        },
        render: function () {
            var self = this;
            this.$el.html(this.template());

            this.loadingDashboard = this.$el.find('.loading-dashboard');
            this.occurrenceTable = this.$el.find('#occurence-table');
            this.siteMarkers = this.$el.find('#site-markers');

            this.originTimelineGraph = this.$el.find('#collection-timeline-graph')[0];
            this.originCategoryGraph = this.$el.find('#collection-category-graph')[0];
            this.recordsTimelineGraph = this.$el.find('#records-timeline-graph')[0];

            this.siteName = this.$el.find('#site-name');
            this.siteNameWrapper = this.siteName.parent();
            this.siteNameWrapper.hide();
            this.totalRecords = this.$el.find('#total-records');

            this.iconStyle = new ol.style.Style({
                image: new ol.style.Icon(({
                    anchor: [0.5, 46],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 0.75,
                    src: '/static/img/map-marker.png'
                }))
            });

            this.siteLayerSource = new ol.source.Vector();
            this.siteLayerVector = new ol.layer.Vector({
                source: this.siteLayerSource,
                style: function (feature) {
                    return self.parent.layers.layerStyle.getBiodiversityStyle(feature);
                }
            });

            return this;
        },
        show: function (data) {
            if (this.isOpen) {
                return false;
            }
            var self = this;
            this.isOpen = true;
            this.$el.show('slide', {
                direction: 'right'
            }, 300, function () {
                if (!self.mapLocationSite) {
                    self.mapLocationSite = new ol.Map({
                        layers: [
                            new ol.layer.Tile({
                                source: new ol.source.OSM()
                            })
                        ],
                        target: 'locationsite-map',
                        view: new ol.View({
                            center: [0, 0],
                            zoom: 2
                        })
                    });
                }
                if (typeof data === 'string') {
                    self.csvDownloadUrl += '?' + data;
                    self.fetchData(data, true);
                } else {
                    self.csvDownloadUrl += self.apiParameters(filterParameters);
                    self.fetchData(self.apiParameters(filterParameters).substr(1), false);
                    Shared.Router.updateUrl('site-detail/' + self.apiParameters(filterParameters).substr(1), true);
                }
            });
        },
        fetchData: function (parameters, multipleSites) {
            var self = this;

            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }

            Shared.LocationSiteDetailXHRRequest = $.get({
                url: self.fetchBaseUrl + parameters,
                dataType: 'json',
                success: function (data) {
                    self.createOccurrenceTable(data);
                    self.createCharts(data);
                    var locationSiteClusterSourceExist = false;
                    if (self.parent.layers.locationSiteClusterSource) {
                        if (self.parent.layers.locationSiteClusterSource.getFeatures().length > 0) {
                            locationSiteClusterSourceExist = true;
                        }
                    }
                    if (locationSiteClusterSourceExist && multipleSites) {
                        // Copy from main map
                        self.copyClusterLayer();
                    } else {
                        self.mapLocationSite.addLayer(self.siteLayerVector);
                        self.fetchLocationSiteCoordinate(self.fetchLocationSiteCoordinateUrl + parameters);
                    }
                    self.loadingDashboard.hide();
                }
            });
        },
        copyClusterLayer: function () {
            var layer = this.parent.layers.locationSiteClusterSource;
            var self = this;
            if (layer) {
                this.siteLayerVector = new ol.layer.Vector({
                    source: this.parent.layers.locationSiteClusterSource,
                    style: function (feature) {
                        return self.parent.layers.layerStyle.getBiodiversityStyle(feature);
                    }
                });
                this.mapLocationSite.addLayer(this.siteLayerVector);
                this.fitSitesToMap();
            }
        },
        fetchLocationSiteCoordinate: function (url) {
            var self = this;

            if (this.locationSiteCoordinateRequestXHR) {
                this.locationSiteCoordinateRequestXHR.abort();
                this.locationSiteCoordinateRequestXHR = null;
            }

            this.locationSiteCoordinateRequestXHR = $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    var results = [];
                    if (data.hasOwnProperty('results')) {
                        results = data['results'];
                    }
                    $.each(results, function (index, siteData) {
                        self.drawMarkers(siteData);
                    });
                    if (self.uniqueSites.length === 1 && !data['next'] && !data['previous']) {
                        self.siteNameWrapper.show();
                        self.siteName.html(results[0].name);
                    }
                    self.locationSiteCoordinateRequestXHR = null;
                    self.fitSitesToMap();
                    if (data['next']) {
                        self.fetchLocationSiteCoordinate(data['next']);
                    }
                }
            });
        },
        fitSitesToMap: function () {
            var source = this.siteLayerVector.getSource();
            var extent = source.getExtent();
            this.mapLocationSite.getView().fit(extent, {
                size: this.mapLocationSite.getSize()
            });
        },
        drawMarkers: function (data) {
            var self = this;

            if (this.uniqueSites.includes(data['id'])) {
                return false;
            }
            this.uniqueSites.push(data['id']);

            // Create marker
            var coordinatesArray = data['coord'].split(',');
            var lon = parseFloat(coordinatesArray[0]);
            var lat = parseFloat(coordinatesArray[1]);
            coords = [lon, lat];
            var pos = ol.proj.fromLonLat(coords);

            var feature = new ol.Feature({
                geometry: new ol.geom.Point(
                    pos
                ),
                id: data['id'],
                name: data['name'],
            });

            this.siteLayerSource.addFeature(feature);
        },
        clearDashboard: function () {
            var self = this;
            this.mapLocationSite.removeLayer(this.siteLayerVector);
            this.siteLayerSource = new ol.source.Vector({});
            this.siteLayerVector = new ol.layer.Vector({
                source: this.siteLayerSource,
                style: function (feature) {
                    return self.parent.layers.layerStyle.getBiodiversityStyle(feature);
                }
            });
            this.siteName.html('');
            this.siteNameWrapper.hide();
            this.uniqueSites = [];
            this.totalRecords.html('0');
            this.siteMarkers.html('');
            this.occurrenceData = {};
            this.occurrenceTable.html('<tr>\n' +
                '                            <th>Taxon</th>\n' +
                '                            <th>Category</th>\n' +
                '                            <th>Records</th>\n' +
                '                        </tr>');

            // Clear canvas
            if (this.originCategoryChart) {
                this.originCategoryChart.destroy();
                this.originCategoryChart = null;
            }

            if (this.recordsTimelineGraphCanvas) {
                this.recordsTimelineGraphCanvas.destroy();
                this.recordsTimelineGraphCanvas = null;
            }

            if (this.originTimelineGraphCanvas) {
                this.originTimelineGraphCanvas.destroy();
                this.originTimelineGraphCanvas = null;
            }

            if (this.mapLocationSite) {
                this.mapLocationSite.getOverlays().getArray().slice(0).forEach(function (overlay) {
                    this.mapLocationSite.removeOverlay(overlay);
                }, this);
            }

            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }

            if (this.locationSiteCoordinateRequestXHR) {
                this.locationSiteCoordinateRequestXHR.abort();
                this.locationSiteCoordinateRequestXHR = null;
            }
        },
        createPieChart: function (container, data, labels, options, colorOptions) {
            return new Chart(container, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colorOptions,
                        borderWidth: 1
                    }]
                },
                options: options
            });
        },
        closeDashboard: function () {
            if (!this.isOpen) {
                return false;
            }
            var self = this;
            this.$el.hide('slide', {
                direction: 'right'
            }, 300, function () {
                self.isOpen = false;
                self.clearDashboard();
                self.loadingDashboard.show();
                Shared.Router.clearSearch();
            });
        },
        createOccurrenceTable: function (data) {
            var self = this;
            var occurrenceData = {};
            var totalRecords = 0;
            if (data.hasOwnProperty('records_occurrence')) {
                occurrenceData = data['records_occurrence']
            }
            $.each(occurrenceData, function (key, value) {
                var recordTable = $('<tr></tr>');
                recordTable.append('<td>' + value['name'] +
                    '</td><td>' + self.categories[value['origin']] + '</td> ' +
                    '<td>' + value['count'] + '</td>');
                totalRecords += value['count'];
                self.occurrenceTable.append(recordTable);
            });
            this.totalRecords.html(totalRecords);
        },
        exportLocationsiteMap: function () {
            $('.ol-control').hide();
            this.mapLocationSite.once('postcompose', function (event) {
                var canvas = document.getElementsByClassName('locationsite-map-wrapper');
                html2canvas(canvas, {
                    useCORS: true,
                    background: '#FFFFFF',
                    allowTaint: false,
                    onrendered: function (canvas) {
                        $('.ol-control').show();
                        var link = document.createElement('a');
                        link.setAttribute("type", "hidden");
                        link.href = canvas.toDataURL("image/png");
                        link.download = 'map.png';
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }
                });
            });
            this.mapLocationSite.renderSync();
        },

        stampCanvas: function(title, graph_canvas)
        {
            var img = new Image();
            var cw, ch=0;
            cw=graph_canvas.width;
            ch=graph_canvas.height;
            console.log('width: ' + cw + '| height: ' + ch);
          //  img.crossOrigin = 'anonymous';
            var tempCanvas=document.createElement('canvas');
            var tempCtx=tempCanvas.getContext('2d');
            var ctx = graph_canvas.getContext('2d');
            img.src='/static/img/fbis-stamp.png';
            img.onload = function() {
                // graph_canvas.height = img.width;
                // graph_canvas.width = img.height;
                ctx.drawImage(img, 0, 0);
                canvas = graph_canvas;
                html2canvas(canvas, {
                    onrendered: function (canvas) {
                        var link = document.createElement('a');
                        link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
                        link.download = title + '.png';
                        link.click();
                    }
                })
            }
        },
        downloadOriginChart: function () {
            var title = 'site-origin-charts';
            var canvas = this.originCategoryGraph;
            this.downloadChart(title, canvas);
        },
        downloadRecordTimeline: function () {
            var title = 'record-timeline';
            var canvas = this.recordsTimelineGraph;
            this.downloadChart(title, canvas);
        },
        downloadCollectionTimeline: function () {
            var title = 'collection-timeline';
            var canvas = this.originTimelineGraph;
            this.downloadChart(title, canvas);
        },
        downloadChart: function (title, graph_canvas) {
            this.stampCanvas(title, graph_canvas);
        },
        downloadingCSV: function (url, downloadButton) {
            var self = this;
            self.downloadCSVXhr = $.get({
                url: self.csvDownloadUrl,
                dataType: 'json',
                success: function (data) {
                    if (data['status'] !== "success") {
                        if (data['status'] === "failed") {
                            if (self.downloadCSVXhr) {
                                self.downloadCSVXhr.abort();
                            }
                            downloadButton.html('Download as CSV');
                            downloadButton.prop("disabled", false);
                        } else {
                            setTimeout(
                                function () {
                                    self.downloadingCSV(url, downloadButton);
                                }, 5000);
                        }
                    } else {
                        var is_safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
                        if (is_safari) {
                            var a = window.document.createElement('a');
                            a.href = '/uploaded/csv_processed/' + data['filename'];
                            a.download = data['filename'];
                            a.click();
                        } else {
                            location.replace('/uploaded/csv_processed/' + data['filename']);
                        }

                        downloadButton.html('Download as CSV');
                        downloadButton.prop("disabled", false);
                    }
                },
                error: function (req, err) {
                }
            });
        },
        downloadAsCSV: function (e) {
            var button = $(e.target);
            button.html('Processing...');
            button.prop("disabled", true);
            this.downloadingCSV(this.csvDownloadUrl, button);
        },
        createCharts: function (data) {
            var self = this;
            var originData = {};
            var originColor = [];
            var originLabel = [];

            var recordsByYearLabel = [];
            var recordsByYearData = [];

            var recordsGraphData = {};
            var dataByOrigin = {};

            if (data.hasOwnProperty('records_graph_data')) {
                recordsGraphData = data['records_graph_data'];
            }

            $.each(recordsGraphData, function (key, value) {
                recordsByYearLabel.push(key);
                var totalData = 0;
                $.each(value, function (objectKey, objectValue) {
                    totalData = 0;
                    if (self.categories[objectKey]) {
                        totalData += objectValue;
                        var category = self.categories[objectKey];
                        if (!originData.hasOwnProperty(category)) {
                            originData[category] = objectValue;
                            originColor.push(self.categoryColor[category]);
                            originLabel.push(category);
                        } else {
                            originData[category] += objectValue;
                        }

                        if (!dataByOrigin[self.categories[objectKey]]) {
                            dataByOrigin[self.categories[objectKey]] = [
                                objectValue
                            ];
                        } else {
                            dataByOrigin[self.categories[objectKey]].push(objectValue);
                        }
                    }
                });
                recordsByYearData.push(totalData);
            });

            this.originCategoryChart = self.createPieChart(
                self.originCategoryGraph.getContext('2d'),
                Object.values(originData),
                originLabel,
                self.pieOptions,
                originColor);

            var recordsByYearDatasets = [{
                backgroundColor: '#48862b',
                borderWidth: 1,
                data: Object.values(recordsByYearData)
            }];

            var recordsByYearGraphOptions = {
                maintainAspectRatio: false,
                title: {display: true, text: 'Records'},
                legend: {display: false},
                scales: {
                    xAxes: [{
                        barPercentage: 0.2,
                        scaleLabel: {
                            display: true,
                            labelString: 'Collection date'
                        }
                    }],
                    yAxes: [{
                        stacked: false,
                        scaleLabel: {
                            display: true,
                            labelString: 'Number of records'
                        },
                        ticks: {
                            beginAtZero: true
                        }
                    }]
                }
            };

            this.recordsTimelineGraphCanvas = new Chart(self.recordsTimelineGraph.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: recordsByYearLabel,
                    datasets: recordsByYearDatasets
                },
                options: recordsByYearGraphOptions
            });

            var originTimelineGraphOptions = {
                maintainAspectRatio: false,
                title: {display: true, text: 'Origin'},
                legend: {display: true},
                scales: {
                    xAxes: [{
                        stacked: true,
                        barPercentage: 0.2,
                        scaleLabel: {
                            display: true,
                            labelString: 'Collection date'
                        }
                    }],
                    yAxes: [{
                        stacked: true,
                        scaleLabel: {display: true, labelString: 'Records'}
                    }]
                }
            };

            var originTimelineDatasets = [];
            $.each(dataByOrigin, function (key, value) {
                originTimelineDatasets.push({
                    label: key,
                    backgroundColor: self.categoryColor[key],
                    borderWidth: 1,
                    data: value
                });
            });

            this.originTimelineGraphCanvas = new Chart(self.originTimelineGraph.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: recordsByYearLabel,
                    datasets: originTimelineDatasets
                },
                options: originTimelineGraphOptions
            })
        }
        ,
    })
});
