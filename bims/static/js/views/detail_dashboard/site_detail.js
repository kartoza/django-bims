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
            'click .ssdd-export': 'downloadElementEvent'
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
                    var graticule = new ol.Graticule({
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
                    self.createOccurrenceDataTable(data);
                    self.createDataSummary(data);
                    if (Object.keys(data['site_details']).length !== 0) {
                        $('#fish-ssdd-site-details').show();
                        self.createFishSSDDSiteDetails(data);
                    } else {
                        $('#fish-ssdd-site-details').hide();
                    }
                    self.createOccurrencesBarChart(data);
                    self.createTaxaStackedBarChart(data);
                    self.createOriginStackedBarChart(data);
                    self.createConsStatusStackedBarChart(data);
                    renderFilterList($('#filter-history-table'));

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
        downloadElementEvent: function (button_el) {
            let target = button_el.target.dataset.datac;
            let element = this.$el.find('#' + target);
            let random_number = Math.random() * 1000000;
            let this_title = `FWBD-Dashboard-Export-{${random_number}}`
            if (element.length > 0)
                this.downloadElement(this_title, element);

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
        renderStackedBarChart: function (dataIn, chartName, chartCanvas) {

            if (!(dataIn.hasOwnProperty('data'))) {
                return false;
            }
            var datasets = [];
            var barChartData = {};
            var colours = ['#D7CD47', '#8D2641', '#18A090', '#3D647D', '#B77282', '#E6E188', '#6BC0B5', '#859FAC']
            var myDataset = {}
            var count = dataIn['dataset_labels'].length;
            for (let i = 0; i < count; i++) {
                myDataset = {};
                var nextKey = dataIn['dataset_labels'][i];
                var nextColour = colours[i];
                var nextData = dataIn['data'][nextKey];
                myDataset = {
                    'label': nextKey,
                    'backgroundColor': nextColour,
                    'data': nextData
                }
                datasets.push(myDataset);
            }
            barChartData = {
                'labels': dataIn['labels'],
                'datasets': datasets,
            }
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
            new ChartJs(ctx, chartConfig);
        },

        createOriginStackedBarChart: function (data) {
            var chartCanvas = document.getElementById('fish-ssdd-origin-bar-chart-canvas');

            if (data.hasOwnProperty('origin_occurrence')) {
                this.renderStackedBarChart(data['origin_occurrence'], 'origin_bar', chartCanvas);
            }
        },

        createTaxaStackedBarChart: function (data) {
            var chartCanvas = document.getElementById('fish-ssdd-taxa-occurrences-line-chart-canvas');
            if (data.hasOwnProperty('taxa_graph')) {
                this.renderStackedBarChart(data['taxa_graph'], 'occurrences_line', chartCanvas);
            }
        },

        createConsStatusStackedBarChart: function (data) {
            var locationContext = {}
            var chartCanvas = document.getElementById('fish-ssdd-cons-status-bar-chart-canvas');
            if (data.hasOwnProperty('cons_status_occurrence')) {
                this.renderStackedBarChart(data['cons_status_occurrence'], 'cons_status_bar', chartCanvas);
            }
        },

        renderBarChart: function (data_in, chartName, chartCanvas) {

            if (!(data_in.hasOwnProperty(chartName + '_chart'))) {
                return false;
            }
            ;

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
                this.renderBarChart(data['taxa_occurrence'], 'occurrences_line', chartCanvas);
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
        },


        createCharts: function (data) {
            var self = this;
            var categorySummary = {};

            var recordsByYearData = {};

            var recordsGraphData = {};
            var dataByOrigin = {};

            if (data.hasOwnProperty('records_graph_data')) {
                recordsGraphData = data['records_graph_data'];
            }
            if (data.hasOwnProperty('category_summary')) {
                categorySummary = data['category_summary'];
            }

            $.each(recordsGraphData, function (key, value) {
                let year = value['year'];
                if (!recordsByYearData.hasOwnProperty(value['year'])) {
                    recordsByYearData[year] = value['count'];
                } else {
                    recordsByYearData[year] += value['count'];
                }
                if (!dataByOrigin.hasOwnProperty(self.categories[value['origin']])) {
                    dataByOrigin[self.categories[value['origin']]] = {};
                }
                dataByOrigin[self.categories[value['origin']]][year] = value['count'];
            });

            let categorySummaryLabels = [];
            let categorySummaryColors = [];

            $.each(categorySummary, function (key, value) {
                categorySummaryLabels.push(self.categories[key]);
                categorySummaryColors.push(self.categoryColor[self.categories[key]]);
            });

            this.originCategoryChart = self.createPieChart(
                self.originCategoryGraph.getContext('2d'),
                Object.values(categorySummary),
                categorySummaryLabels,
                self.pieOptions,
                categorySummaryColors);

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
                    labels: Object.keys(recordsByYearData),
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

            /*
                Example Data :
                dataByOrigin = {
                    'Native': {2014: 3, 2016: 4},
                    'Non-Native': {2014: 3, 2016: 1}
                };
            */
            $.each(dataByOrigin, function (key, value) {
                originTimelineDatasets.push({
                    label: key,
                    backgroundColor: self.categoryColor[key],
                    borderWidth: 1,
                    data: Object.values(value)
                });
            });

            this.originTimelineGraphCanvas = new Chart(self.originTimelineGraph.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: Object.keys(recordsByYearData),
                    datasets: originTimelineDatasets
                },
                options: originTimelineGraphOptions
            })
        },
        renderTableFromTitlesValuesLists: function (specific_data, all_data = [], alias_type = '', bold_title = true) {
            var title = '';
            var value = '';
            var temp_result;
            var title_class = ''
            var $result = $('<div></div>');
            if (bold_title == true) {
                title_class = 'title_column';
            }
            var count = specific_data['value'].length;
            for (let i = 0; i < count; i++) {
                title = this.parseNameFromAliases(specific_data['title'][i], alias_type, all_data);
                value = specific_data['value'][i];
                temp_result = `<div class="row">
                               <div class="col-6 ${title_class}">${title}</div>
                               <div class="col-6">${value}</div>
                               </div>`
                $result.append(temp_result);
            }
            return $result;
        },

        createFishSSDDSiteDetails: function (data) {
            var siteDetailsWrapper = $('#fish-ssdd-site-details');


            var overview = siteDetailsWrapper.find('#overview');
            overview.html(this.renderTableFromTitlesValuesLists(
                data['site_details']['overview']));
            var catchments = siteDetailsWrapper.find('#catchments');
            catchments.html(this.renderTableFromTitlesValuesLists(
                data['site_details']['catchments']),
                data);
            var sub_water_management_areas = siteDetailsWrapper.find(
                '#sub_water_management_areas');
            sub_water_management_areas.html(this.renderTableFromTitlesValuesLists(
                data['site_details']['sub_water_management_areas']));
            var sa_ecoregions = siteDetailsWrapper.find('#sa-ecoregions');
            sa_ecoregions.html(this.renderTableFromTitlesValuesLists(
                data['site_details']['sa_ecoregions']));

            var recordSitesWrapper = $('#fish-ssdd-records-sites')
            var recordSitesSub = recordSitesWrapper.find('#records-sites');
            recordSitesSub.html(this.renderTableFromTitlesValuesLists(data['site_details']['records_and_sites']))

            var originsWrapper = $('#fish-ssdd-origins');
            var originsSub = originsWrapper.find('#origins');
            originsSub.html(this.renderTableFromTitlesValuesLists(data['site_details']['origins_data'], data, 'origin', false));

            var conservation_statusWrapper = $('#fish-ssdd-conservation-status');
            var conservation_statusSub = conservation_statusWrapper.find('#ssdd-conservation-status');
            conservation_statusSub.html(this.renderTableFromTitlesValuesLists(data['site_details']['conservation_status_data'], data, 'cons_status', false));

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
            var bio_data = data['biodiversity_data'];
            var biodiversity_fish_data = data['biodiversity_data']['fish'];
            var origin_length = biodiversity_fish_data['origin_chart']['keys'].length;
            for (let i = 0; i < origin_length; i++) {
                let next_name = biodiversity_fish_data['origin_chart']['keys'][i];
                biodiversity_fish_data['origin_chart']['keys'][i] =
                    self.parseNameFromAliases(next_name, 'origin', data);
            }

            var cons_status_length = biodiversity_fish_data['cons_status_chart']['keys'].length;
            for (let i = 0; i < cons_status_length; i++) {
                let next_name = biodiversity_fish_data['cons_status_chart']['keys'][i];
                biodiversity_fish_data['cons_status_chart']['keys'][i] =
                    self.parseNameFromAliases(next_name, 'cons_status', data);
            }
            var origin_pie_canvas = document.getElementById('fish-ssdd-origin-pie');

            this.renderPieChart(bio_data, 'fish', 'origin', origin_pie_canvas);

            var endemism_pie_canvas = document.getElementById('fish-ssdd-endemism-pie');
            this.renderPieChart(bio_data, 'fish', 'endemism', endemism_pie_canvas);

            var conservation_status_pie_canvas = document.getElementById('fish-ssdd-conservation-status-pie');
            this.renderPieChart(bio_data, 'fish', 'cons_status', conservation_status_pie_canvas);
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
        renderTableFromTitlesValuesLists: function (specific_data, all_data = [], alias_type = '', bold_title = true) {
            var title = '';
            var value = '';
            var temp_result;
            var title_class = ''
            var $result = $('<div></div>');
            if (bold_title == true) {
                title_class = 'title_column';
            }
            var count = specific_data['value'].length;
            for (let i = 0; i < count; i++) {
                title = this.parseNameFromAliases(specific_data['title'][i], alias_type, all_data);
                value = specific_data['value'][i];
                temp_result = `<div class="row">
                               <div class="col-6 ${title_class}">${title}</div>
                               <div class="col-6">${value}</div>
                               </div>`
                $result.append(temp_result);
            }
            return $result;
        },
        createOccurrenceDataTable: function (data) {
            var renderedOccurrenceData = this.renderOccurrenceData(data);
            var occurrenceDataWrapper = $('#fish-ssdd-occurrence-data');
            var occurrenceDataSub = occurrenceDataWrapper.find('#occurrence-data');
            occurrenceDataSub.html(renderedOccurrenceData);
        },
        renderOccurrenceData: function (data) {
            data_in = data['occurrence_data'];
            var result = '<div>';
            if (typeof data_in == 'undefined') {
                return result + '</div>'
            }
            var count = 0;
            var column_count = 0;
            var column_class = '';
            var column_value = '';
            var next_col = '';
            // Render headings
            try {
                count = data_in['titles'].length;
            } catch (e) {
                count = 0;
            }
            result += '<div class="row">'; //Open new row
            for (let i = 0; i < count; i++) {

                column_class = 'col-2 title-column';
                if ('titles' in data_in) {
                    column_value = data_in['titles'][i];
                } else {
                    column_class = 'Unknown';
                }
                // Make my first column wider
                if (i == 0) {
                    column_class = 'col-4 title-column';
                }
                next_col = `<div class="${column_class}">
                            <div class="center-self">${column_value}
                            </div></div>`;
                result += next_col;
            }
            result += '</div>' //Close my row
            // Render rows
            column_count = count;
            count = data_in['data'].length;
            var taxon_values = [];

            for (let i = 0; i < count; i++) {
                result += '<div class="row">'; //Open new row
                taxon_values = data_in['data'][i];
                var column_key = ''
                for (let j = 0; j < column_count; j++) {
                    column_class = 'col-2';
                    column_value = 'Unknown';
                    if ('data_keys' in data_in) {
                        column_key = data_in['data_keys'][j];
                        if (typeof taxon_values != 'undefined') {
                            if (column_key in taxon_values) {
                                column_value = this.parseNameFromAliases(
                                    taxon_values[column_key],
                                    column_key,
                                    data);
                            }
                        }
                    }
                    // Make my first column wider
                    if (j == 0) {
                        column_class = 'col-4';
                    }
                    next_col = `<div class="${column_class}">
                                <div class="center-self">${column_value}
                                </div></div>`;
                    result += next_col;
                }
                result += '</div>'; //Close row
            }
            result += '</div>'; //Close row
            var $result = $.parseHTML(result);

            return $result
        },
        parseNameFromAliases: function (alias, alias_type, data) {
            var name = alias;
            var choices = [];
            var index = 0;
            if (alias_type == 'cons_status') {
                choices = this.flatten_arr(data['iucn_name_list']);
            }
            if (alias_type == 'origin') {
                choices = this.flatten_arr(data['origin_name_list']);
            }
            if (choices.length > 0) {
                index = choices.indexOf(alias) + 1;
                name = choices[index];
            }
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
        }
    })
});
