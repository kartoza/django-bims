define([
    'backbone',
    'underscore',
    'ol',
    'jquery',
    'shared',
    'htmlToCanvas',
    'chartJs',
], function (
    Backbone,
    _,
    ol,
    $,
    Shared,
    HtmlToCanvas,
    ChartJs,
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
            'Translocated': '#e0d43f',
            'No origin data': '#565656',
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
            'translocated': 'Translocated',
            null: 'No origin data'
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

            let biodiversityLayersOptions = {
                url: geoserverPublicUrl + 'wms',
                params: {
                    LAYERS: locationSiteGeoserverLayer,
                    FORMAT: 'image/png8',
                    viewparams: 'where:' + emptyWMSSiteParameter
                },
                ratio: 1,
                serverType: 'geoserver'
            };
            this.siteLayerSource = new ol.source.ImageWMS(biodiversityLayersOptions);
            this.siteTileLayer = new ol.layer.Image({
                source: self.siteLayerSource
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
                    self.mapLocationSite.addLayer(self.siteTileLayer);
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

            if (is_sass_enabled) {
                var obj = {};
                parameters.replace(/([^=&]+)=([^&]*)/g, function (m, key, value) {
                    obj[decodeURIComponent(key)] = decodeURIComponent(value);
                });
                let siteIds = obj['siteId'].split(',');
                var sassDashboardButton = self.$el.find('.sass-dashboard-button');
                if (siteIds.length === 1 && siteIds[0] !== '') {
                    sassDashboardButton.find('a').attr('href', '/sass/dashboard/' + siteIds[0] + '/?' + parameters);
                } else {
                    sassDashboardButton.find('a').attr('href', '/sass/dashboard-multi-sites/?' + parameters);
                }
            }

            Shared.LocationSiteDetailXHRRequest = $.get({
                url: self.fetchBaseUrl + parameters,
                dataType: 'json',
                success: function (data) {
                    self.createOccurrencesBarChart(data);
                    // Zoom to extent
                    let ext = ol.proj.transformExtent(data['extent'], ol.proj.get('EPSG:4326'), ol.proj.get('EPSG:3857'));
                    self.mapLocationSite.getView().fit(ext, self.mapLocationSite.getSize());
                    if (self.mapLocationSite.getView().getZoom() > 8) {
                        self.mapLocationSite.getView().setZoom(8);
                    }

                    let newParams = {
                        layers: locationSiteGeoserverLayer,
                        format: 'image/png',
                        viewparams: 'where:"' + data['sites_raw_query'] + '"'
                    };
                    self.siteLayerSource.updateParams(newParams);

                    self.loadingDashboard.hide();
                }
            });
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
                let newParams = {
                    layers: locationSiteGeoserverLayer,
                    format: 'image/png',
                    viewparams: 'where:' + emptyWMSSiteParameter
                };
                self.siteLayerSource.updateParams(newParams);
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
            var img = new Image();
            var ctx = graph_canvas.getContext('2d');
            img.src = '/static/img/bims-stamp.png';
            img.onload = function () {
                ctx.drawImage(img, graph_canvas.scrollWidth - img.width - 5,
                    graph_canvas.scrollHeight - img.height - 5);
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
        renderBarChart: function(data_in, chartName, chartCanvas) {

             if (!(data_in.hasOwnProperty(chartName + '_chart')))
            {
               return false;
            };

             var chartConfig = {
                type: 'bar',
                data: {
                    datasets: [{
                        data: data_in[chartName + '_chart']['values'],
                        backgroundColor: '#D7CD47',
                        borderColor: '#D7CD47',
                        fill: false
                    }],
                    labels: data_in[chartName + '_chart']['keys']
                },
                options: {
                    responsive: true,
                    legend:{ display: false },
                    title: { display: false },
                    hover: { mode: 'point', intersect: false},
                    tooltips: {
                        mode: 'point',
                    },
                    borderWidth: 0,
                    scales: {
					xAxes: [{
						display: true,
						scaleLabel: {
							display: false,
							labelString: ''
						}
					}],

					yAxes: [{
						display: true,
						scaleLabel: {
							display: true,
							labelString: data_in[chartName + '_chart']['title']
						},
						ticks: {
                          beginAtZero: true,
                          callback: function(value) {if (value % 1 === 0) {return value;}}
                        }
					}]
                    }
                }
             };
             chartCanvas = this.resetCanvas(chartCanvas);
             var ctx = chartCanvas.getContext('2d');
             ctx.height = '200px';
             new ChartJs(ctx, chartConfig);
        },
        createOccurrencesBarChart: function (data) {
            var chartCanvas = document.getElementById('fish-ssdd-occurrences-line-chart-canvas');

             if (data.hasOwnProperty('records_occurrence')) {
                this.renderBarChart(data['records_occurrence'], 'occurrences_line', chartCanvas);
             }

         },
        resetCanvas: function (chartCanvas) {
            var chartParent = chartCanvas.parentElement;
            var newCanvas = document.createElement("CANVAS");
            var chartId = chartCanvas.id;
            newCanvas.id = chartId;
            chartCanvas.remove();
            chartParent.append(newCanvas);
            return document.getElementById(chartId);
        }
    })
});
