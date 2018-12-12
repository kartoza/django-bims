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
        template: _.template($('#detailed-site-dashboard').html()),
        dummyPieData: [25, 2, 7, 10, 12, 25, 60],
        objectDataByYear: 'object_data_by_year',
        yearsArray: 'years_array',
        dummyPieColors: ['#2d2d2d', '#565656', '#6d6d6d', '#939393', '#adadad', '#bfbfbf', '#d3d3d3'],
        fetchBaseUrl: '/api/location-site-detail/?',
        csvDownloadUrl: '/api/collection/download/',
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
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
                    Shared.Router.navigate('site-detail/' + self.apiParameters(filterParameters).substr(1));
                    self.generateDashboard(data);
                    self.loadingDashboard.hide();
                }
            });
        },
        fetchData: function (parameters) {
            var self = this;

            // call detail
            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }

            Shared.LocationSiteDetailXHRRequest = $.get({
                url: self.fetchBaseUrl + parameters,
                dataType: 'json',
                success: function (data) {
                    self.generateDashboard(data);
                    self.loadingDashboard.hide();
                }
            });
        },
        generateDashboard: function (data) {
            var self = this;

            self.siteName.html(data['name']);

            // Total records
            var totalRecords = 0;
            $.each(data['modules_info'], function (moduleKey, moduleValue) {
                totalRecords += parseInt(moduleValue['count']);
            });
            self.totalRecords.html(totalRecords);

            if(!this.mapLocationSite) {
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
            if(this.siteVectorLayer){
                this.mapLocationSite.removeLayer(this.siteVectorLayer);
                this.siteVectorLayer = null;
            }
            var geometry = JSON.parse(data['geometry']);
            var siteCoordinate = ol.proj.transform([geometry['coordinates'][0], geometry['coordinates'][1]], 'EPSG:4326', 'EPSG:3857');
            var siteFeature = new ol.Feature({
                geometry: new ol.geom.Point(siteCoordinate)
            });
            siteFeature.setStyle(self.iconStyle);
            this.siteVectorSource = new ol.source.Vector({
                features: [siteFeature]
            });
            this.siteVectorLayer = new ol.layer.Vector({
                source: this.siteVectorSource
            });

            this.mapLocationSite.addLayer(this.siteVectorLayer);
            this.mapLocationSite.setView(new ol.View({
                center: siteCoordinate,
                zoom: 12
            }));

            self.createCharts(data);
            self.createOccurrenceTable(data);
        },
        clearDashboard: function () {
            this.siteName.html('');
            this.totalRecords.html('');

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
        },
        createPieChart: function(container, data, labels, options, colorOptions) {
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
            var occurenceTable = $('<table></table>');
            occurenceTable.append('' +
                '<tr>' +
                '<th>Taxon</th><th>Category</th><th>Records</th>' +
                '</tr>');
            var recordOccurences = data['records_occurrence'];
            $.each(recordOccurences, function (key, value) {
                for (record_key in value) {
                    if (!value.hasOwnProperty(record_key)) {
                        return true;
                    }
                    var recordTable = $('<tr></tr>');
                    recordTable.append('<td>' + record_key +
                        '</td><td>' + self.categories[value[record_key]['category']] + '</td> ' +
                        '<td>' + value[record_key]['count'] + '</td>');
                     occurenceTable.append(recordTable);
                }
            });
            $('#occurence-table').html(occurenceTable);
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
                        if(is_safari) {
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

            $.each(data['records_occurrence'], function (key, value) {
                for (record_key in value) {
                    if (!value.hasOwnProperty(record_key)) {
                        return true;
                    }

                    var objectProperties = value[record_key];
                    var category = self.categories[objectProperties['category']];

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
                            if(originByYearData[category].hasOwnProperty(dataByYearKey)) {
                                originByYearData[category][dataByYearKey] += intDataByYear;
                            } else {
                                originByYearData[category][dataByYearKey] = intDataByYear;
                            }
                        } else {
                            originByYearData[category] = {};
                            originByYearData[category][dataByYearKey] = intDataByYear;
                        }
                    });
                }
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
                title: { display: true, text: 'Records' },
                legend: { display: false },
                scales: {
                    xAxes: [{
                        barPercentage: 0.2,
                        scaleLabel: { display: true, labelString: 'Collection date' }
                    }],
                    yAxes: [{
                        stacked: false,
                        scaleLabel: { display: true, labelString: 'Number of records' },
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
                title: { display: true, text: 'Origin' },
                legend: { display: true },
                scales: {
                    xAxes: [{
                        stacked: true,
                        barPercentage: 0.2,
                        scaleLabel: { display: true, labelString: 'Collection date' }
                    }],
                    yAxes: [{
                        stacked: true,
                        scaleLabel: { display: true, labelString: 'Records' }
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
