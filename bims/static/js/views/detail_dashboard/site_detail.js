define([
    'backbone',
    'underscore',
    'ol',
    'jquery',
    'shared',
    'htmlToCanvas',
    'chartJs',
    'utils/filter_list'
], function (
    Backbone,
    _,
    ol,
    $,
    Shared,
    HtmlToCanvas,
    ChartJs,
    filterList
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
        currentFiltersUrl: '',
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
            'click .download-as-csv': 'downloadAsCSV',
            'click .ssdd-export': 'downloadElementEvent',
            'click .download-chart-image': 'downloadChartImage',
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
                        controls: ol.control.defaults().extend([
                            new ol.control.ScaleLine()
                        ]),
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
                    let graticule = new ol.Graticule({
                        strokeStyle: new ol.style.Stroke({
                            color: 'rgba(0,0,0,1)',
                            width: 1,
                            lineDash: [2.5, 4]
                        }),
                        showLabels: true
                    });
                    graticule.setMap(self.mapLocationSite);
                }
                if (typeof data === 'string') {
                    self.csvDownloadUrl += '?' + data;
                    self.fetchData(data, true);
                    self.currentFiltersUrl = '?' + data;
                } else {
                    self.csvDownloadUrl += self.apiParameters(filterParameters);
                    self.currentFiltersUrl = self.apiParameters(filterParameters);
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
                    if (data.hasOwnProperty('status')) {
                        if (data['status'] === 'processing') {
                            setTimeout(function () {
                                self.fetchData(parameters);
                            }, 2000);
                            return false;
                        }
                    }

                    self.createOccurrenceDataTable(data);
                    self.createDataSummary(data);

                    let dashboardHeader = self.$el.find('.dashboard-header');
                    if (data['is_multi_sites']) {
                        $('#fish-ssdd-site-details').hide();
                        self.createMultiSiteDetails(data);
                        let sassDashboardButton = $('#sass-dashboard-button');
                        sassDashboardButton.show();
                        if (!data['is_sass_exists']) {
                            sassDashboardButton.addClass('disabled');
                        } else {
                            let sassLink = '/sass/dashboard-multi-sites/' + self.currentFiltersUrl;
                            sassDashboardButton.attr('href', sassLink);
                        }
                        dashboardHeader.html('Multiple Sites Dashboard');
                    } else {
                        $('#fish-ssdd-site-details').show();
                        self.createFishSSDDSiteDetails(data);
                        dashboardHeader.html('Single Site Dashboard');
                    }

                    renderFilterList($('#filter-history-table'));
                    self.createOccurrencesBarChart(data);
                    self.createTaxaStackedBarChart();
                    self.createConsStatusStackedBarChart(data);
                    self.createEndemismStackedBarChart();
                    self.createOriginStackedBarChart(data);

                    // Zoom to extent
                    if (data['extent'].length > 0) {
                        let ext = ol.proj.transformExtent(
                            data['extent'],
                            ol.proj.get('EPSG:4326'),
                            ol.proj.get('EPSG:3857'));
                        self.mapLocationSite.getView().fit(ext, self.mapLocationSite.getSize());
                        if (self.mapLocationSite.getView().getZoom() > 8) {
                            self.mapLocationSite.getView().setZoom(8);
                        }
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
            this.$el.find('.chart-loading').show();
            let sassDashboardButton = $('#sass-dashboard-button');
            sassDashboardButton.hide();
            sassDashboardButton.removeClass('disabled');
            sassDashboardButton.attr('href', '#');
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

            if (this.taxaOccurrencesChartCanvas) {
                this.taxaOccurrencesChartCanvas.destroy();
                this.taxaOccurrencesChartCanvas = null;
            }

            if (this.consChartCanvas) {
                this.consChartCanvas.destroy();
                this.consChartCanvas = null;
            }

            if (this.originChartCanvas) {
                this.originChartCanvas.destroy();
                this.originChartCanvas = null;
            }

            if (this.endemismChartCanvas) {
                this.endemismChartCanvas.destroy();
                this.endemismChartCanvas = null;
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
        closeDashboard: function () {
            if (!this.isOpen) {
                return false;
            }
            this.$el.find('#detailed-site-dashboard-wrapper')[0].scrollIntoView();
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
        exportLocationsiteMap: function () {
            $('.ol-control').hide();
            this.mapLocationSite.once('postrender', function (event) {
                let canvas = $('#locationsite-map');
                html2canvas(canvas, {
                    useCORS: false,
                    background: '#FFFFFF',
                    allowTaint: true,
                    onrendered: function (canvas) {
                        $('.ol-control').show();
                        let link = document.createElement('a');
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
        downloadElementEvent: function (button_el) {
            let button = $(button_el.target);
            if (!button.hasClass('btn')) {
                button = button.parent();
            }
            let target = button.data('datac');
            let element = this.$el.find('#' + target);
            let random_number = Math.random() * 1000000;
            let this_title = `FWBD-Dashboard-Export-{${random_number}}`;
            if (element.length > 0)
                this.downloadElement(this_title, element);
        },
        downloadChartImage: function (e) {
            let button = $(e.target);
            if (!button.hasClass('btn')) {
                button = button.parent();
            }
            let target = button.data('datac');
            let title = button.data('title');
            let element = this.$el.find('.' + target);

            // Get image
            let image = element.children('img').attr('src');

            if (image) {
                let link = document.createElement('a');
                link.href = image;
                link.download = title + '.png';
                link.click();
            }
        },
        downloadElement: function (title, element) {
            element[0].scrollIntoView();
            html2canvas(element, {
                onrendered: function (canvas) {
                    var link = document.createElement('a');
                    link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
                    link.download = title + '.png';
                    link.click();
                }
            })
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
        renderStackedBarChart: function (dataIn, chartName, chartCanvas, randomColor = false) {
            if (!(dataIn.hasOwnProperty('data'))) {
                return false;
            }
            var datasets = [];
            var barChartData = {};
            var colours = ['#D7CD47', '#8D2641', '#18A090', '#3D647D', '#B77282', '#E6E188', '#6BC0B5', '#859FAC'];
            var myDataset = {};
            var count = dataIn['dataset_labels'].length;
            for (let i = 0; i < count; i++) {
                myDataset = {};
                var nextKey = dataIn['dataset_labels'][i];
                var nextColour = colours[i%colours.length];
                if (randomColor) {
                    nextColour = Shared.ColorUtil.generateHexColor();
                }
                var nextData = dataIn['data'][nextKey];
                myDataset = {
                    'label': nextKey,
                    'backgroundColor': nextColour,
                    'data': nextData
                };
                datasets.push(myDataset);
            }
            barChartData = {
                'labels': dataIn['labels'],
                'datasets': datasets,
            };
            var chartConfig = {
                type: 'bar',
                data: barChartData,
                options: {
                    responsive: true,
                    legend: {display: true},
                    title: {display: false},
                    hover: {mode: 'point', intersect: false},
                    tooltips: {
                        mode: 'point',
                        position: 'average',
                    },
                    borderWidth: 0,
                    scales: {
                        xAxes: [{
                            stacked: true,
                        }],
                        yAxes: [{
                            stacked: true,
                            ticks: {
                                beginAtZero: true,
                                callback: function (value) {
                                    if (value % 1 === 0) {
                                        return value;
                                    }
                                },
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Occurrences',
                            },
                        }]
                    }
                }

            };
            chartCanvas = this.resetCanvas(chartCanvas);
            var ctx = chartCanvas.getContext('2d');
            return new ChartJs(ctx, chartConfig);
        },
        fetchChartData: function (chartContainer, baseUrl, callback) {
            let width = chartContainer.width();
            width += 150; // padding
            let loadingChart = chartContainer.find('.chart-loading');
            baseUrl += this.currentFiltersUrl;
            baseUrl += '&width=' + width;
            baseUrl += '&base_64=1';
            $.get({
                url: baseUrl,
                cache: true,
                processData: false,
                success: function (data) {
                    loadingChart.hide();
                    callback(data);
                },
                error: function () {
                    loadingChart.hide();
                    chartContainer.html('No Data');
                }
            });
        },
        createOriginStackedBarChart: function (data) {
            let self = this;
            let originCategoryList = data['origin_name_list'];
            let chartContainer = this.$el.find('.fish-ssdd-origin-bar-chart');
            let baseUrl = '/api/location-sites-occurrences-chart-data/';

            this.fetchChartData(
                chartContainer,
                baseUrl,
                (responseData) => {
                    if (Object.keys(responseData['data']).length === 0) {
                        self.$el.find('.fish-ssdd-origin-bar-chart').hide();
                        return;
                    }
                    self.$el.find('.fish-ssdd-origin-bar-chart').show();
                    // Update labels
                    $.each(responseData['dataset_labels'], function (index, label) {
                        if (originCategoryList.hasOwnProperty(label)) {
                            responseData['dataset_labels'][index] = originCategoryList[label];
                        }
                    });
                    $.each(responseData['data'], function (key, current_data) {
                        if (originCategoryList.hasOwnProperty(key)) {
                            delete responseData['data'][key];
                            responseData['data'][originCategoryList[key]] = current_data;
                        }
                    });
                    let chartCanvas = document.getElementById('fish-ssdd-origin-bar-chart-canvas');
                    this.originChartCanvas = self.renderStackedBarChart(responseData, 'origin_bar', chartCanvas);
                }
            );
        },
        createTaxaStackedBarChart: function () {
            let self = this;
            let chartContainer = this.$el.find('#fish-ssdd-taxa-occurrences-bar-chart');
            let baseUrl = '/api/location-sites-taxa-chart-data/';
            let chartCanvas = document.getElementById('fish-ssdd-taxa-occurrences-line-chart-canvas');

            this.fetchChartData(
                chartContainer,
                baseUrl,
                (responseData) => {
                    if(Object.keys(responseData['data']).length === 0) {
                        self.$el.find('.fish-ssdd-taxa-line-chart').hide();
                        return;
                    }
                    self.$el.find('.fish-ssdd-taxa-line-chart').show();
                    this.taxaOccurrencesChartCanvas = self.renderStackedBarChart(responseData, 'occurrences_line', chartCanvas);
                }
            )
        },
        createConsStatusStackedBarChart: function (data) {
            let self = this;
            let iucnCategoryList = data['iucn_name_list'];
            let chartContainer = this.$el.find('#fish-ssdd-cons-status-bar-chart');
            let baseUrl = '/api/location-sites-cons-chart-data/';

            this.fetchChartData(
                chartContainer,
                baseUrl,
                (responseData) => {
                    if (Object.keys(responseData['data']).length === 0) {
                        self.$el.find('.fish-ssdd-cons-status-bar-chart').hide();
                        return;
                    }
                    self.$el.find('.fish-ssdd-cons-status-bar-chart').show();
                    // Update labels
                    $.each(responseData['dataset_labels'], function (index, label) {
                        if (iucnCategoryList.hasOwnProperty(label)) {
                            responseData['dataset_labels'][index] = iucnCategoryList[label];
                        }
                    });
                    // Update data title
                    $.each(responseData['data'], function (key, data) {
                        if (iucnCategoryList.hasOwnProperty(key)) {
                            delete responseData['data'][key];
                            responseData['data'][iucnCategoryList[key]] = data;
                        }
                    });
                    var chartCanvas = document.getElementById('fish-ssdd-cons-status-bar-chart-canvas');
                    this.consChartCanvas = self.renderStackedBarChart(responseData, 'cons_status_bar', chartCanvas);
                }
            )
        },
        createEndemismStackedBarChart: function () {
            let self = this;
            let chartContainer = this.$el.find('#fish-ssdd-endemism-bar-chart');
            let baseUrl = '/api/location-sites-endemism-chart-data/';
            let chartCanvas = document.getElementById('fish-ssdd-endemism-bar-chart-canvas');

            this.fetchChartData(
                chartContainer,
                baseUrl,
                (responseData) => {
                    if(Object.keys(responseData['data']).length === 0) {
                        self.$el.find('.fish-ssdd-endemism-bar-chart').hide();
                        return;
                    }
                    self.$el.find('.fish-ssdd-endemism-bar-chart').show();
                    this.endemismChartCanvas = self.renderStackedBarChart(responseData, 'endemism', chartCanvas);
                }
            )
        },
        renderBarChart: function (data_in, chartName, chartCanvas) {

            if (!(data_in.hasOwnProperty(chartName + '_chart'))) {
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
                    legend: {display: false},
                    title: {display: false},
                    hover: {mode: 'point', intersect: false},
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
                                callback: function (value) {
                                    if (value % 1 === 0) {
                                        return value;
                                    }
                                }
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
            if (data.hasOwnProperty('taxa_occurrence')) {
                if (data['taxa_occurrence']['occurrences_line_chart']['values'].length === 0) {
                    this.$el.find('.fish-ssdd-occurrences-line-chart').hide();
                    return;
                }
                this.$el.find('.fish-ssdd-occurrences-line-chart').show();
                this.renderBarChart(data['taxa_occurrence'], 'occurrences_line', chartCanvas);
            }
        },
        createMultiSiteDetails: function (data) {
            let overview = this.$el.find('#records-sites');
            overview.html(this.renderTableFromTitlesValuesLists(data['site_details']['overview']));

            this.createOriginsOccurrenceTable(data);
            this.createConservationOccurrenceTable(data);
            this.createEndemismOccurrenceTable(data);
        },
        createFishSSDDSiteDetails: function (data) {
            let siteDetailsWrapper = $('#fish-ssdd-overview');

            let overview = siteDetailsWrapper.find('#overview');
            overview.html(this.renderTableFromTitlesValuesLists(data['site_details']['overview']));
            let catchments = siteDetailsWrapper.find('#catchments');
            let catchmentsData = data['site_details']['catchments'];
            let orderedCatchments = {};
            orderedCatchments['Primary'] = catchmentsData['Primary'];
            orderedCatchments['Secondary'] = catchmentsData['Secondary'];
            orderedCatchments['Tertiary'] = catchmentsData['Tertiary'];
            orderedCatchments['Quaternary'] = catchmentsData['Quaternary'];
            catchments.html(this.renderTableFromTitlesValuesLists(orderedCatchments));

            let sub_water_management_areas = siteDetailsWrapper.find('#sub_water_management_areas');
            sub_water_management_areas.html(this.renderTableFromTitlesValuesLists(data['site_details']['sub_water_management_areas']));

            let sa_ecoregions = siteDetailsWrapper.find('#sa-ecoregions');
            sa_ecoregions.html(this.renderTableFromTitlesValuesLists(data['site_details']['sa_ecoregions']));

            let recordSitesWrapper = $('#fish-ssdd-records-sites');
            let recordSitesSub = recordSitesWrapper.find('#records-sites');
            recordSitesSub.html(this.renderTableFromTitlesValuesLists(data['site_details']['records_and_sites']));

            this.createOriginsOccurrenceTable(data);
            this.createConservationOccurrenceTable(data);
            this.createEndemismOccurrenceTable(data);
        },
        createOriginsOccurrenceTable: function (data) {
            let originsSub = this.$el.find('#origins');
            let originCategoryList = data['origin_name_list'];
            let originChartData = data['biodiversity_data']['species']['origin_chart'];
            let originsTableData = {};
            $.each(originChartData['keys'], function (index, value) {
                let category = value;
                if(originCategoryList.hasOwnProperty(value)) {
                    category = originCategoryList[value];
                }
                originsTableData[category] = originChartData['data'][index];
            });
            originsSub.html(this.renderTableFromTitlesValuesLists(originsTableData, false));
        },
        createConservationOccurrenceTable: function (data) {
            let conservation_statusSub = this.$el.find('#ssdd-conservation-status');
            let consChartData = data['biodiversity_data']['species']['cons_status_chart'];
            let consCategoryList = data['iucn_name_list'];
            let constTableData = {};
            $.each(consChartData['keys'], function (index, value) {
                let category = value;
                if(consCategoryList.hasOwnProperty(value)) {
                    category = consCategoryList[value];
                }
                constTableData[category] = consChartData['data'][index];
            });
            constTableData = this.sortOnKeys(constTableData);
            conservation_statusSub.html(this.renderTableFromTitlesValuesLists(constTableData, false));
        },
        createEndemismOccurrenceTable: function (data) {
            let endemismDataChart = data['biodiversity_data']['species']['endemism_chart'];
            let endemismData = {};
            if (!endemismDataChart) {
                return false;
            }
            $.each(endemismDataChart['keys'], function (index, data) {
                endemismData[data] = endemismDataChart['data'][index];
            });
            let wrapper = this.$el.find('#ssdd-endemism');
            wrapper.html(this.renderTableFromTitlesValuesLists(endemismData, false));
        },
        renderSiteDetailInfo: function (data) {
            var $detailWrapper = $('<div></div>');
            if (data.hasOwnProperty('site_detail_info')) {
                var siteDetailsTemplate = _.template($('#site-details-template').html());
                $detailWrapper.html(siteDetailsTemplate({
                    'fbis_site_code': data['site_detail_info']['fbis_site_code'],
                    'site_coordinates': data['site_detail_info']['site_coordinates'],
                    'site_description': data['site_detail_info']['site_description'],
                    'geomorphological_zone': data['site_detail_info']['geomorphological_zone'],
                    'river': data['site_detail_info']['river'],
                }));
            }
            return $detailWrapper;
        },
        createDataSummary: function (data) {
            let bio_data = data['biodiversity_data'];
            let biodiversityData = data['biodiversity_data']['species'];
            let origin_length = biodiversityData['origin_chart']['keys'].length;
            let originNameList = data['origin_name_list'];
            for (let i = 0; i < origin_length; i++) {
                let next_name = biodiversityData['origin_chart']['keys'][i];
                if (originNameList.hasOwnProperty(next_name)) {
                    biodiversityData['origin_chart']['keys'][i] = originNameList[next_name];
                }
            }
            let iucnCategory = data['iucn_name_list'];
            let cons_status_length = biodiversityData['cons_status_chart']['keys'].length;
            for (let i = 0; i < cons_status_length; i++) {
                let next_name = biodiversityData['cons_status_chart']['keys'][i];
                if (iucnCategory.hasOwnProperty(next_name)) {
                    biodiversityData['cons_status_chart']['keys'][i] = iucnCategory[next_name];
                }
            }
            let origin_pie_canvas = document.getElementById('fish-ssdd-origin-pie');
            this.renderPieChart(bio_data, 'species', 'origin', origin_pie_canvas);
            let endemism_pie_canvas = document.getElementById('fish-ssdd-endemism-pie');
            this.renderPieChart(bio_data, 'species', 'endemism', endemism_pie_canvas);
            let conservation_status_pie_canvas = document.getElementById('fish-ssdd-conservation-status-pie');
            this.renderPieChart(bio_data, 'species', 'cons_status', conservation_status_pie_canvas);
            let sampling_method_pie_canvas = document.getElementById('fish-ssdd-sampling-method-pie');
            this.renderPieChart(bio_data, 'species', 'sampling_method', sampling_method_pie_canvas);
        },
        renderPieChart: function (data, speciesType, chartName, chartCanvas) {
            if (typeof data == 'undefined') {
                return null;
            }
            var backgroundColours = [
                '#8D2641',
                '#D7CD47',
                '#18A090',
                '#A2CE89',
                '#4E6440',
                '#525351']
            var chartConfig = {
                type: 'pie',
                data: {
                    datasets: [{
                        data: data[speciesType][chartName + '_chart']['data'],
                        backgroundColor: backgroundColours
                    }],
                    labels: data[speciesType][chartName + '_chart']['keys']
                },
                options: {
                    responsive: true,
                    legend: {display: false},
                    title: {display: false},
                    hover: {mode: 'nearest', intersect: false},
                    borderWidth: 0,
                }
            };
            chartCanvas = this.resetCanvas(chartCanvas);
            var ctx = chartCanvas.getContext('2d');
            new ChartJs(ctx, chartConfig);

            // Render chart labels
            var dataKeys = data[speciesType][chartName + '_chart']['keys'];
            var dataLength = dataKeys.length;
            var chart_labels = {};
            chart_labels[chartName] = ''
            for (var i = 0; i < dataLength; i++) {
                chart_labels[chartName] += '<div><span style="color:' +
                    backgroundColours[i] + ';">■</span>' +
                    '<span class="fish-ssdd-legend-title">&nbsp;' +
                    dataKeys[i] + '</span></div>'
            }
            var element_name = `#fish-ssdd-${chartName}-legend`;
            $(element_name).html(chart_labels[chartName]);
        },
        renderTableFromTitlesValuesLists: function (specific_data, bold_title = true) {
            var temp_result;
            var title_class = '';
            var $result = $('<div></div>');
            if (bold_title === true) {
                title_class = 'title_column';
            }
            $.each(specific_data, function (key, value) {
                temp_result = `<div class="row">
                               <div class="col-6 ${title_class}">${key}</div>
                               <div class="col-6">${value}</div>
                               </div>`;
                $result.append(temp_result);
            });
            return $result;
        },
        createOccurrenceDataTable: function (data) {
            let occurrenceDataWrapper = $('#fish-ssdd-occurrence-data');
            let occurrenceDataSub = occurrenceDataWrapper.find('#occurrence-data');
            if (data['occurrence_data'].length > 0 || data['iucn_name_list'].length > 0 || data['origin_name_list'].length > 0) {
                this.$el.find('.download-as-csv').show();
                occurrenceDataSub.html(this.renderOccurrenceData(data['occurrence_data'], data['iucn_name_list'], data['origin_name_list']));
            } else {
                occurrenceDataSub.html('No Data');
                this.$el.find('.download-as-csv').hide();
            }
        },
        renderOccurrenceData: function (occurrenceData, conservationStatusList, originCategoryList) {
            let occurrenceTable = $('<table class="table table-bordered table-condensed table-sm site-detailed-table">');
            occurrenceTable.append("<thead>\n" +
                "      <tr>\n" +
                "        <th>Taxon</th>\n" +
                "        <th>Origin</th>\n" +
                "        <th>Occurrences</th>\n" +
                "        <th>Endemism</th>\n" +
                "        <th>Cons. Status</th>\n" +
                "      </tr>\n" +
                "    </thead>");
            let tableBody = $('<tbody>');
            $.each(occurrenceData, function (index, rowData) {
                let tRow = $('<tr>');
                let originName = rowData['origin'];
                if (originCategoryList.hasOwnProperty(originName)) {
                    originName = originCategoryList[originName];
                }
                let consName = rowData['cons_status'];
                if (conservationStatusList.hasOwnProperty(consName)) {
                    consName = conservationStatusList[consName];
                } else {
                    consName = 'Data deficient';
                }
                tRow.append('<td>' + rowData['taxon'] + '</td>');
                tRow.append('<td>' + originName + '</td>');
                tRow.append('<td>' + rowData['count'] + '</td>');
                tRow.append('<td>' + rowData['endemism'] + '</td>');
                tRow.append('<td>' + consName + '</td>');
                tableBody.append(tRow);
            });
            occurrenceTable.append(tableBody);
            return occurrenceTable;
        },
        parseNameFromAliases: function (alias, alias_type, data) {
            name = '';
            // var name = alias;
            // var choices = [];
            // var index = 0;
            // if (alias_type === 'cons_status') {
            //     choices = this.flatten_arr(data['iucn_name_list']);
            // }
            // if (alias_type === 'origin') {
            //     choices = this.flatten_arr(data['origin_name_list']);
            // }
            // if (choices.length > 0) {
            //     index = choices.indexOf(alias) + 1;
            //     name = choices[index];
            // }
            return name;
        },
        flatten_arr: function (arr) {
            self = this;
            return arr.reduce(function (flat, toFlatten) {
                return flat.concat(Array.isArray(toFlatten) ? self.flatten_arr(toFlatten) : toFlatten);
            }, []);
        },
        resetCanvas: function (chartCanvas) {
            var chartParent = chartCanvas.parentElement;
            var newCanvas = document.createElement("CANVAS");
            var chartId = chartCanvas.id;
            newCanvas.id = chartId;
            chartCanvas.remove();
            chartParent.append(newCanvas);
            return document.getElementById(chartId);
        },
        sortOnKeys: function (dict) {
            var sorted = [];
            for (var key in dict) {
                sorted[sorted.length] = key;
            }
            sorted.sort();
            var tempDict = {};
            for (var i = 0; i < sorted.length; i++) {
                tempDict[sorted[i]] = dict[sorted[i]];
            }
            return tempDict;
        }
    })
});
