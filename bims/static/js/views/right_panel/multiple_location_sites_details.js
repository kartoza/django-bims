define(['backbone', 'shared', 'chartJs', 'jquery', 'underscore', 'utils/filter_list'], function (Backbone, Shared, ChartJs, $, _, filterList) {
    return Backbone.View.extend({
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        charts: [],
        originLegends: {},
        endemismLegends: {},
        consStatusLegends: {},
        chartColors: null,
        chartBackgroundColours: [
            '#8D2641',
            '#D7CD47',
            '#18A090',
            '#A2CE89',
            '#4E6440',
            '#525351'],
        initialize: function () {
            Shared.Dispatcher.on('multiSiteDetailPanel:show', this.show, this);
            this.fetchChartColors();
        },
        fetchChartColors: function () {
            var self = this;
            $.ajax({
                url: '/api/chart-colors/',
                method: 'GET',
                success: function (data) {
                    self.chartColors = data;
                },
                error: function () {
                    // Fallback to default colors if API fails
                    self.chartColors = [
                        '#8D2641', '#641f30',
                        '#E6E188', '#D7CD47',
                        '#9D9739', '#525351',
                        '#618295', '#2C495A',
                        '#39B2A3', '#17766B',
                        '#859FAC', '#1E2F38'
                    ];
                }
            });
        },
        show: function () {
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:toggleLoading', true);
            this.originLegends = {};
            this.endemismLegends = {};
            this.consStatusLegends = {};
            if (filterParameters.hasOwnProperty('siteIdOpen')) {
                filterParameters['siteIdOpen'] = '';
                filterParameters['siteId'] = '';
            }
            this.fetchData();
        },
        hideAll: function (e) {
            let className = $(e.target).attr('class');
            let target = $(e.target);
            if (className === 'search-result-title') {
                target = target.parent();
            }
            if (target.data('visibility')) {
                target.find('.filter-icon-arrow').addClass('fa-angle-down');
                target.find('.filter-icon-arrow').removeClass('fa-angle-up');
                target.nextAll().hide();
                target.data('visibility', false)
            } else {
                target.find('.filter-icon-arrow').addClass('fa-angle-up');
                target.find('.filter-icon-arrow').removeClass('fa-angle-down');
                target.nextAll().show();
                target.data('visibility', true)
            }
        },
        renderFilterHistorySection: function (container) {
            let $filterDetailWrapper = $(
                '<div class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"><span class="search-result-title"> Filter History </span><i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div>' +
                '</div>');
            container.append($filterDetailWrapper);
            let $filterDetailTable = $('<table class="table table-condensed table-sm filter-history-table"></table>');
            let $filterDetailTableContainer = $('<div class="container-fluid" style="padding-top: 10px;"></div>');
            $filterDetailTableContainer.append($filterDetailTable);
            $filterDetailWrapper.append($filterDetailTableContainer);
            renderFilterList($filterDetailTable);
        },
        renderBiodiversityDataSection: function (container, data) {
            let self = this;
            let biodiversitySectionTemplate = _.template($('#biodiversity-data-template-new').html());
            let $sectionWrapper = $(
                '<div id="biodiversity-data" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> Biodiversity Data </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            container.append($sectionWrapper);
            $sectionWrapper.append(biodiversitySectionTemplate(
              {
                  ecosystem_type: '',
                  data: data.biodiversity_data,
                  is_sass_enabled: is_sass_enabled,
                  is_water_temperature_enabled: is_water_temperature_enabled,
                  is_climate_enabled: is_climate_enabled,
                  is_pesticide_dashboard_enabled: is_pesticide_dashboard_enabled,
                  sass_exist: data.sass_exist,
                  physico_chemical_exist: false,
                  add_data: false,
                  water_temperature_exist: false,
                  climate_exist: false
              }));
            $.each(data['biodiversity_data'], function (key, value) {
                self.charts.push({
                    'canvas': $sectionWrapper.find("#origin-chart-" + value.module),
                    'data': value['origin'],
                    'legends': self.originLegends
                });
                self.charts.push({
                    'canvas': $sectionWrapper.find("#endemism-chart-" + value.module),
                    'data': value['endemism'],
                    'legends': self.endemismLegends
                });
                self.charts.push({
                    'canvas': $sectionWrapper.find("#cons-chart-" + value.module),
                    'data': value['cons_status'],
                    'legends': self.consStatusLegends
                });
            });
            $sectionWrapper.find('.sp-open-dashboard').click(function (e) {
                let parameters = $.extend(true, {}, filterParameters);
                const $target = $(e.target);
                if ($target.hasClass("disabled")) {
                    return false;
                }
                parameters['modules'] = $target.data('module');
                Shared.Router.updateUrl('site-detail/' + self.apiParameters(parameters).substr(1), true);
            });
            $sectionWrapper.find('.spatial-dashboard-btn').click(function () {
                let url = '/spatial-dashboard/';
                url += self.apiParameters(filterParameters);
                window.location.href = url;
            });
            $sectionWrapper.find('.sp-sass-dashboard').click(function () {
                let sassUrl = '';
                if (typeof self.siteId !== 'undefined') {
                    sassUrl = '/sass/dashboard/' + self.siteId + '/';
                } else {
                    sassUrl = '/sass/dashboard-multi-sites/';
                }
                sassUrl += self.apiParameters(filterParameters);
                window.location.href = sassUrl;
            });
        },
        createPieChart: function (chartData) {
            let self = this;
            let labels = [];
            let dataset = [];
            let colours = [];
            let data = chartData['data'];
            let chartCanvas = chartData['canvas'];
            let legends = chartData['legends'];
            $.each(data, function (key, value) {
                labels.push(value['name']);
                dataset.push(value['count']);

                if(value.hasOwnProperty('colour')) {
                    colours.push(value['colour']);
                    legends[value['name']] = value['colour'];
                } else {
                    if (legends.hasOwnProperty(value['name'])) {
                        colours.push(legends[value['name']]);
                    } else {
                        let length = Object.keys(legends).length;
                        let chartColors = self.chartColors || self.chartBackgroundColours;
                        colours.push(chartColors[length]);
                        legends[value['name']] = chartColors[length];
                    }
                }
            });

            let chartConfig = {
                type: 'pie',
                data: {
                    datasets: [{
                        data: dataset,
                        backgroundColor: colours
                    }],
                    labels: labels
                },
                options: {
                    responsive: false,
                    legend: {display: false},
                    title: {display: false},
                    hover: {mode: 'nearest', intersect: false},
                    borderWidth: 0,
                }
            };
            let ctx = chartCanvas[0].getContext('2d');
            new ChartJs(ctx, chartConfig);
        },
        renderCharts: function () {
            let self = this;
            $.each(this.charts, function (index, chart) {
                if (chart['data'].length > 0) {
                    self.createPieChart(chart);
                }
            })
        },
        renderLegends: function (legends, container) {
            $.each(legends, function (key, value) {
                container.append('<div><span style="color:' +
                    value + ';">■</span>' +
                    '<span style="font-style: italic;">' +
                    key + '</span></div>');
            });
        },
        renderPanel: function (data) {
            let $siteDetailWrapper = $('<div>');
            this.renderFilterHistorySection($siteDetailWrapper);
            this.renderBiodiversityDataSection($siteDetailWrapper, data);

            Shared.Dispatcher.trigger('sidePanel:toggleLoading', false, 'Multi-Site Overview');
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $siteDetailWrapper);
            $siteDetailWrapper.find('.search-results-total').click(this.hideAll);
            $siteDetailWrapper.find('.search-results-total').click();

            // This need to be done after html rendered
            this.renderCharts();
            this.renderLegends(this.originLegends, $('.origin-legends'));
            this.renderLegends(this.endemismLegends, $('.endemism-legends'));
            this.renderLegends(this.consStatusLegends, $('.cons-status-legends'));
        },
        fetchData: function () {
            let self = this;
            if (Shared.MultiSitesOverviewXHRRequest) {
                Shared.MultiSitesOverviewXHRRequest.abort();
                Shared.MultiSitesOverviewXHRRequest = null;
            }
            Shared.MultiSitesOverviewXHRRequest = $.get({
                url: multiSitesOverviewBackgroundUrl + self.apiParameters(filterParameters),
                dataType: 'json',
                success: function (data) {
                    if (data.hasOwnProperty('status')) {
                        if (data['status'] === 'processing') {
                            setTimeout(function () {
                                self.fetchData();
                            }, 500);
                            return
                        }
                    }
                    self.renderPanel(data);
                }
            });
        }
    });
});
