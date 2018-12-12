define([
    'backbone',
    'underscore',
    'ol',
    'jquery',
    'shared'
], function (
    Backbone,
    _,
    ol,
    $,
    Shared
) {
    return Backbone.View.extend({
        id: 'detailed-site-dashboard',
        isOpen: false,
        coordinates: [],
        template: _.template($('#detailed-site-dashboard').html()),
        dummyPieData: [25, 2, 7, 10, 12, 25, 60],
        objectDataByYear: 'object_data_by_year',
        yearsArray: 'years_array',
        dummyPieColors: ['#2d2d2d', '#565656', '#6d6d6d', '#939393', '#adadad', '#bfbfbf', '#d3d3d3'],
        fetchBaseUrl: '/api/location-site-detail/?',
        csvDownloadUrl: '/api/collection/download/',
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        occurrenceData: {},
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
            maintainAspectRatio: false,
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
        initialize: function () {
            this.$el.hide();
            this.mapLocationSite = null;
        },
        render: function () {
            this.$el.html(this.template());

            this.loadingDashboard = this.$el.find('.loading-dashboard');
            this.occurrenceTable = this.$el.find('#occurence-table');
            this.siteMarkers = this.$el.find('#site-markers');

            this.originTimelineGraph = this.$el.find('#collection-timeline-graph')[0];
            this.originCategoryGraph = this.$el.find('#collection-category-graph')[0];
            this.recordsTimelineGraph = this.$el.find('#records-timeline-graph')[0];

            this.siteName = this.$el.find('#site-name');
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
                if (typeof data === 'string') {
                    self.csvDownloadUrl += '?' + data;
                    self.fetchData(data);
                } else {
                    self.csvDownloadUrl += self.apiParameters(filterParameters);
                    Shared.Router.navigate('site-detail/' + self.apiParameters(filterParameters).substr(1))
                    self.siteName.append(data['name']);;
                    self.generateDashboardData(data);
                    self.renderDashboard();
                    self.loadingDashboard.hide();
                }
            });
        },
        checkMultipleSites: function (parameters) {
            // Get the site id
            var parameterList = parameters.split('&');
            var siteIds = [];
            var urls = [];

            $.each(parameterList, function (index, parameter) {
                if (typeof parameter === 'undefined') {
                    return true;
                }
                // siteId=4155 -> ['siteId', '4155']
                var parameterValueKey = parameter.split('=');

                var parameterKey = parameterValueKey[0];
                var parameterValue = parameterValueKey[1];

                if (parameterKey === 'siteId') {
                    siteIds = parameterValue.split(',');
                    parameterList.splice(index, 1);
                }
            });

            // Generate the urls
            $.each(siteIds, function (index, siteId) {
                var url = parameterList.join('&');
                url += '&siteId=' + siteId;

                urls.push(url);
            });

            return urls;
        },
        fetchLocationDetail: function (urls, index) {
            var self = this;
            if (!index) {
                index = 0;
            }
            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }

            Shared.LocationSiteDetailXHRRequest = $.get({
                url: self.fetchBaseUrl + urls[index],
                dataType: 'json',
                success: function (data) {
                    self.generateDashboardData(data, urls[index]);
                    self.siteName.append(data['name']);
                    if (typeof urls[index + 1] !== 'undefined') {
                        self.fetchLocationDetail(urls, index + 1);
                        self.siteName.append(', ');
                    } else {
                        self.loadingDashboard.hide();
                        self.renderDashboard();
                    }
                }
            });
        },
        fetchData: function (parameters) {
            var self = this;
            // Check if multiple sites
            var urls = self.checkMultipleSites(parameters);

            if (urls.length > 1) {
                $('#site-name-label').html('Site names');
            }
            self.fetchLocationDetail(urls);
        },
        generateDashboardData: function (data, url) {
            var self = this;
            // Try draw points in map
            self.drawMarkers(data, url);

            // Set total records
            $.each(data['modules_info'], function (moduleKey, moduleValue) {
                var totalNumberRecords = parseInt(self.totalRecords.html());
                self.totalRecords.html(totalNumberRecords + parseInt(moduleValue['count']));
            });

            // Count occurrence data
            $.each(data['records_occurrence'], function (key, classOccurrence) {
                for (var speciesName in classOccurrence) {
                    if (!classOccurrence.hasOwnProperty(speciesName)) {
                        return true;
                    }
                    var speciesOccurrence = classOccurrence[speciesName];
                    if (!self.occurrenceData.hasOwnProperty(speciesOccurrence['taxon_id'])) {
                        self.occurrenceData[speciesOccurrence['taxon_id']] = {
                            'label': speciesName,
                            'count': speciesOccurrence['count'],
                            'category': self.categories[speciesOccurrence['category']],
                            'data_by_year': speciesOccurrence['data_by_year']
                        }
                    } else {
                        self.occurrenceData[speciesOccurrence['taxon_id']]['count'] +=
                            speciesOccurrence['count'];
                    }

                }
            });

        },
        renderDashboard: function () {
            this.createOccurrenceTable(this.occurrenceData);
            this.createCharts(this.occurrenceData);

            var bbox = ol.extent.boundingExtent(this.coordinates);
            this.mapLocationSite.getView().fit(bbox, this.mapLocationSite.getSize());
            var currentZoom = this.mapLocationSite.getView().getZoom();
            if (currentZoom > 10) {
                this.mapLocationSite.getView().setZoom(10);
            }
        },
        drawMarkers: function (data, url) {
            var self = this;
            if (!this.mapLocationSite) {
                this.mapLocationSite = new ol.Map({
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

            // Create marker
            var geometry = JSON.parse(data['geometry']);
            var pos = ol.proj.fromLonLat(geometry['coordinates']);

            this.coordinates.push(ol.proj.transform(geometry['coordinates'], 'EPSG:4326', 'EPSG:3857'));

            self.siteMarkers.append('<a class="overlay site-marker-name" id="marker-name-' + data['id'] + '" ' +
                'target="_blank" href="/map/#site-detail/' + url + '">' + data['name'] + '</a>');
            self.siteMarkers.append('<div id="marker-point-' + data['id'] + '" title="Marker" class="site-marker"></div>');
            var marker = new ol.Overlay({
                position: pos,
                positioning: 'center-center',
                element: self.$el.find('#marker-point-' + data['id'])[0],
                stopEvent: false
            });
            this.mapLocationSite.addOverlay(marker);
            var markerName = new ol.Overlay({
                position: pos,
                element: self.$el.find('#marker-name-' + data['id'])[0]
            });
            this.mapLocationSite.addOverlay(markerName);
        },
        clearDashboard: function () {
            this.siteName.html('');
            this.coordinates = [];
            $('#site-name-label').html('Name');
            this.totalRecords.html('0');
            this.siteMarkers.html('');
            this.occurrenceData = {};
            this.occurrenceTable.html('<tr>\n' +
                '                            <th>Taxon</th>\n' +
                '                            <th>Category</th>\n' +
                '                            <th>Records</th>\n' +
                '                        </tr>');

            // Clear canvas
            if (this.originCategoryGraphCanvas) {
                this.originCategoryGraphCanvas.destroy();
                this.originCategoryGraphCanvas = null;
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
        createOccurrenceTable: function (occurrenceData) {
            var self = this;
            $.each(occurrenceData, function (key, value) {
                var recordTable = $('<tr></tr>');
                recordTable.append('<td>' + value['label'] +
                    '</td><td>' + value['category'] + '</td> ' +
                    '<td>' + value['count'] + '</td>');
                self.occurrenceTable.append(recordTable);
            });
        },
        exportLocationsiteMap: function () {
            this.mapLocationSite.once('postcompose', function (event) {
                var canvas = event.context.canvas;
                if (navigator.msSaveBlob) {
                    navigator.msSaveBlob(canvas.msToBlob(), 'map.png');
                } else {
                    canvas.toBlob(function (blob) {
                        saveAs(blob, 'map.png')
                    })
                }
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
        downloadChart: function (title, canvas) {
            html2canvas(canvas, {
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
        createCharts: function (data) {
            var self = this;
            var originData = {};
            var originColor = [];
            var originLabel = [];

            var recordsByYearLabel = [];
            var recordsByYearData = {};

            var originByYearData = {};

            $.each(data, function (key, value) {

                var objectProperties = value;
                var category = objectProperties['category'];

                if (!originData.hasOwnProperty(category)) {
                    originData[category] = objectProperties['count'];
                    originColor.push(self.categoryColor[category]);
                    originLabel.push(category);
                } else {
                    originData[category] += objectProperties['count'];
                }

                var dataByYear = objectProperties['data_by_year'];
                $.each(dataByYear, function (dataByYearKey, dataByYearValue) {
                    var intDataByYear = parseInt(dataByYearValue);

                    if (recordsByYearData.hasOwnProperty(dataByYearKey)) {
                        recordsByYearData[dataByYearKey] += intDataByYear;
                    } else {
                        recordsByYearData[dataByYearKey] = intDataByYear;
                        recordsByYearLabel.push(dataByYearKey);
                    }

                    if (originByYearData.hasOwnProperty(category)) {
                        if (originByYearData[category].hasOwnProperty(dataByYearKey)) {
                            originByYearData[category][dataByYearKey] += intDataByYear;
                        } else {
                            originByYearData[category][dataByYearKey] = intDataByYear;
                        }
                    } else {
                        originByYearData[category] = {};
                        originByYearData[category][dataByYearKey] = intDataByYear;
                    }
                });
            });

            this.originCategoryGraphCanvas = self.createPieChart(
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

            $.each(originByYearData, function (_originKey, _originData) {
                var _datasetsData = [];
                $.each(recordsByYearLabel, function (index, value) {
                    if (!_originData.hasOwnProperty(value)) {
                        _datasetsData.push(0);
                    } else {
                        _datasetsData.push(_originData[value]);
                    }
                });
                originTimelineDatasets.push({
                    label: _originKey,
                    backgroundColor: self.categoryColor[_originKey],
                    borderWidth: 1,
                    data: _datasetsData
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
        },
    })
});
