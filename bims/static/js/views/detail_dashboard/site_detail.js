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
        template: _.template($('#detailed-site-dashboard').html()),
        dummyPieData: [25, 2, 7, 10, 12, 25, 60],
        objectDataByYear: 'object_data_by_year',
        yearsArray: 'years_array',
        dummyPieColors: ['#2d2d2d', '#565656', '#6d6d6d', '#939393', '#adadad', '#bfbfbf', '#d3d3d3'],
        fetchBaseUrl: '/api/location-site-detail/?',
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
            'click .close-dashboard': 'closeDashboard'
        },
        initialize: function () {
            this.$el.hide();
        },
        render: function () {
            this.$el.html(this.template());

            this.loadingDashboard = this.$el.find('.loading-dashboard');
            this.originTimelineGraph = this.$el.find('#fish-timeline-graph')[0];
            this.originCategoryGraph = this.$el.find('#fish-category-graph')[0];
            this.recordsTimelineGraph = this.$el.find('#records-timeline-graph')[0];

            return this;
        },
        show: function (data) {
            var self = this;
            this.$el.show('slide', {
                direction: 'right'
            }, 300, function () {
                if (typeof data === 'string') {
                    self.fetchData(data);
                } else {
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

            self.createPieChart(
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

            new Chart(self.recordsTimelineGraph.getContext('2d'), {
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

            new Chart(self.originTimelineGraph.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: recordsByYearLabel,
                    datasets: originTimelineDatasets
                },
                options: originTimelineGraphOptions
            })
        },
        generateDashboard: function (data) {
            var self = this;
            self.createCharts(data);
        },
        clearDashboard: function () {
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
        countObjectPerDateCollection: function(data, categoryOrigin, categories) {
            var originDataDate = [];
            var dataByDate = {};

            $.each(data, function (key, value) {
                var collection_year = new Date(value['collection_date']).getFullYear();
                if($.inArray(collection_year, originDataDate) === -1){
                    originDataDate.push(collection_year)
                }
            });

            $.each(originDataDate, function (idx, year) {
                dataByDate[year] = {};
                $.each(categoryOrigin, function (index, origin) {
                    dataByDate[year][origin] = 0;
                    $.each(data, function (key, value) {
                        var valueYear = new Date(value['collection_date']).getFullYear();
                        if(categories[value['category']] === origin && valueYear === year){
                            dataByDate[year][origin] += 1;
                        }
                    })
                });
            });

            var results = {};
            results[this.objectDataByYear] = dataByDate;

            console.log(results);
            return results;
        },
        closeDashboard: function () {
            var self = this;
            this.$el.hide('slide', {
                direction: 'right'
            }, 300, function () {
                self.clearDashboard();
                self.loadingDashboard.show();
            });
        },
    })
});
