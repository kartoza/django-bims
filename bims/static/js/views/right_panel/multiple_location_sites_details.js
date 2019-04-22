define(['backbone', 'shared', 'chartJs', 'jquery', 'underscore', 'utils/filter_list'], function (Backbone, Shared, ChartJs, $, _, filterList) {
    return Backbone.View.extend({
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        charts: [],
        originLegends: {},
        endemismLegends: {},
        consStatusLegends: {},
        chartBackgroundColours: [
            '#8D2641',
            '#D7CD47',
            '#18A090',
            '#A2CE89',
            '#4E6440',
            '#525351'],
        initialize: function () {
            Shared.Dispatcher.on('multiSiteDetailPanel:show', this.show, this);
        },
        show: function () {
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', '<i class="fa fa-map-marker"></i> Loading...');
            this.originLegends = {};
            this.endemismLegends = {};
            this.consStatusLegends = {};
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
            let $filterDetailTable = $('<table class="table table-condensed table-sm table-bordered"></table>');
            let $filterDetailTableContainer = $('<div class="container-fluid" style="padding-top: 10px;"></div>');
            $filterDetailTableContainer.append($filterDetailTable);
            $filterDetailWrapper.append($filterDetailTableContainer);
            renderFilterList($filterDetailTable);
        },
        renderBiodiversityDataSection: function (container, data) {
            let self = this;
            let $sectionWrapper = $(
                '<div id="biodiversity-data" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> Biodiversity Data </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            container.append($sectionWrapper);

            let $sectionContainer = $('<div class="container-fluid"></div>');
            $sectionWrapper.append($sectionContainer);

            let $table = $('<table class="table table-striped table-condensed table-sm"></table>');
            $sectionContainer.append($table);

            // create row
            let $iconHead = $('<thead></thead>');
            let $occurrenceRow = $('<tr></tr>');
            let $siteRow = $('<tr></tr>');
            let $originRow = $('<tr></tr>');
            let $endemismRow = $('<tr></tr>');
            let $consStatusRow = $('<tr></tr>');
            let $numTaxaRow = $('<tr></tr>');
            let $dashboardRow = $('<tr></tr>');
            $table.append($iconHead);
            $table.append($occurrenceRow);
            $table.append($siteRow);
            $table.append($originRow);
            $table.append($endemismRow);
            $table.append($consStatusRow);
            $table.append($numTaxaRow);
            $table.append($dashboardRow);

            $iconHead.append('<td></td>');
            $occurrenceRow.append('<td>Occurrences</td>');
            $siteRow.append('<td>Sites</td>');
            $originRow.append('<td>Origin<div class="origin-legends"></div></td>');
            $endemismRow.append('<td>Endemism<div class="endemism-legends"></div></td>');
            $consStatusRow.append('<td>Cons. Status<div class="cons-status-legends"></div></td>');
            $numTaxaRow.append('<td>Number of Taxa</td>');
            $dashboardRow.append('<td style="padding-top: 12px;">Dashboard</td>');

            $.each(data['biodiversity_data'], function (key, value) {
                $iconHead.append('<td class="overview-data"><img width="30" src="/uploaded/' + value['icon'] + '"></td></td>');
                $occurrenceRow.append('<td class="overview-data">' + value['occurrences'] + '</td>');
                $siteRow.append('<td class="overview-data">' + value['sites'] + '</td>');
                $numTaxaRow.append('<td class="overview-data">' + value['number_of_taxa'] + '</td>');

                let $dashboardButton = $('<button class="fbis-button-small" style="width: 100%">' + key + '</button>');
                if (value['occurrences'] === 0) {
                    $dashboardButton.addClass('disabled');
                } else {
                    $dashboardButton.click(function () {
                        let parameters = $.extend(true, {}, filterParameters);
                        parameters['modules'] = value['module'];
                        Shared.Router.updateUrl('site-detail/' + self.apiParameters(parameters).substr(1), true);
                    });
                }
                let $dashboardRowContainer = $('<td>');
                $dashboardRowContainer.append($dashboardButton);
                $dashboardRow.append($dashboardRowContainer);

                let $originColumn = $('<td class="overview-data"></td>');
                let $originCanvas = $('<canvas class="overview-chart"></canvas>');
                $originColumn.append($originCanvas);
                $originRow.append($originColumn);
                self.charts.push({
                    'canvas': $originCanvas,
                    'data': value['origin'],
                    'legends': self.originLegends
                });

                let $endemismColumn = $('<td class="overview-data"></td>');
                let $endemismCanvas = $('<canvas class="overview-chart"></canvas>');
                $endemismColumn.append($endemismCanvas);
                $endemismRow.append($endemismColumn);
                self.charts.push({
                    'canvas': $endemismCanvas,
                    'data': value['endemism'],
                    'legends': self.endemismLegends
                });

                let $consStatusColumn = $('<td class="overview-data"></td>');
                let $consStatusCanvas = $('<canvas class="overview-chart"></canvas>');
                $consStatusColumn.append($consStatusCanvas);
                $consStatusRow.append($consStatusColumn);
                self.charts.push({
                    'canvas': $consStatusCanvas,
                    'data': value['cons_status'],
                    'legends': self.consStatusLegends
                });

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

                if (legends.hasOwnProperty(value['name'])) {
                    colours.push(legends[value['name']]);
                } else {
                    let length = Object.keys(legends).length;
                    colours.push(self.chartBackgroundColours[length]);
                    legends[value['name']] = self.chartBackgroundColours[length];
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

            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', '<i class="fa fa-map-marker"></i> Multi-Site Overview');
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
                url: multiSitesOverviewDataUrl + self.apiParameters(filterParameters),
                dataType: 'json',
                success: function (data) {
                    self.renderPanel(data);
                }
            });
        }
    });
});
