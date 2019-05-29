define(['backbone', 'ol', 'shared', 'chartJs', 'jquery'], function (Backbone, ol, Shared, ChartJs, $) {
    return Backbone.View.extend({
        id: 0,
        currentSpeciesSearchResult: [],
        siteChartData: {},
        siteId: null,
        siteName: null,
        siteDetailData: null,
        charts: [],
        originLegends: {},
        endemismLegends: {},
        consStatusLegends: {},
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        months: {
            'january': 1,
            'february': 2,
            'march': 3,
            'april': 4,
            'may': 5,
            'june': 6,
            'july': 7,
            'august': 8,
            'september': 9,
            'october': 10,
            'november': 11,
            'december': 12
        },
        chartBackgroundColours: [
            '#8D2641',
            '#D7CD47',
            '#18A090',
            '#A2CE89',
            '#4E6440',
            '#525351'],
        initialize: function () {
            Shared.Dispatcher.on('siteDetail:show', this.show, this);
            Shared.Dispatcher.on('siteDetail:updateCurrentSpeciesSearchResult', this.updateCurrentSpeciesSearchResult, this);
        },
        updateCurrentSpeciesSearchResult: function (newList) {
            this.currentSpeciesSearchResult = newList;
        },
        show: function (id, name, zoomToObject) {
            this.originLegends = {};
            this.endemismLegends = {};
            this.consStatusLegends = {};
            this.siteId = id;
            this.siteName = name;
            this.zoomToObject = zoomToObject;
            this.parameters = filterParameters;
            this.parameters['siteId'] = id;
            filterParameters = $.extend(true, {}, this.parameters);
            this.url = '/api/location-site-detail/' + this.apiParameters(this.parameters);
            this.showDetail(name, zoomToObject)
        },
        hideAll: function (e) {
            var className = $(e.target).attr('class');
            var target = $(e.target);
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
                    responsive: false,
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
            chart_labels[chartName] = '';
            for (var i = 0; i < dataLength; i++) {
                chart_labels[chartName] += '<div><span style="color:' +
                    backgroundColours[i] + ';">■</span>' +
                    '<span class="fish-ssdd-legend-title">&nbsp;' +
                    dataKeys[i] + '</span></div>'
            }
            var element_name = `#rp-${chartName}-legend`;
            $(element_name).html(chart_labels[chartName]);
        },

        renderSiteDetailInfo: function (data) {
            var $detailWrapper = $('<div></div>');
            if (data.hasOwnProperty('site_detail_info')) {
                var siteDetailsTemplate = _.template($('#site-details-template').html());
                let siteName = data['name'];
                let siteDescription = data['site_detail_info']['site_description'];
                if (siteDescription === 'Unknown') {
                    if (siteName) {
                        siteDescription = siteName;
                    }
                }
                let geomorphologicalZone = '-';
                let ecologicalRegion = '-';
                try {
                    if(data['refined_geomorphological']) {
                        geomorphologicalZone = data['refined_geomorphological'];
                    } else {
                        geomorphologicalZone = data['location_context_document_json']['context_group_values']['eco_geo_group']['service_registry_values']['geo_class_recoded']['value'];
                    }
                    ecologicalRegion = data['location_context_document_json']['context_group_values']['eco_geo_group']['service_registry_values']['eco_region']['value'];
                } catch (err) {
                }

                $detailWrapper.append(siteDetailsTemplate({
                    'fbis_site_code': data['site_detail_info']['fbis_site_code'],
                    'site_name': data['name'],
                    'site_coordinates': data['site_detail_info']['site_coordinates'],
                    'site_description': siteDescription,
                    'geomorphological_zone': geomorphologicalZone,
                    'ecological_region': ecologicalRegion,
                    'river': data['site_detail_info']['river'],
                }));
            }
            return $detailWrapper;
        },

        renderClimateData: function (data) {
            var locationContext = {};
            var $detailWrapper = $('<div></div>');

            if (data.hasOwnProperty('climate_data')) {
                var climateDataTemplate = _.template($('#climate-data-template').html());
                $detailWrapper.append(climateDataTemplate({
                    'mean_annual_temperature': data['climate_data']['mean_annual_temperature'],
                    'mean_annual_rainfall': data['climate_data']['mean_annual_rainfall']
                }));
            }
            ;
            return $detailWrapper;
        },
        createDataSummary: function (data) {
            var bio_data = data['biodiversity_data'];
            var origin_pie_canvas = document.getElementById('fish-rp-origin-pie');
            this.renderPieChart(bio_data, 'fish', 'origin', origin_pie_canvas);

            var endemism_pie_canvas = document.getElementById('fish-rp-endemism-pie');
            this.renderPieChart(bio_data, 'fish', 'endemism', endemism_pie_canvas);

            var conservation_status_pie_canvas = document.getElementById('fish-rp-conservation-status-pie');
            this.renderPieChart(bio_data, 'fish', 'cons_status', conservation_status_pie_canvas);
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
        renderMonthlyLineChart: function (data_in, chartName) {
            if (!(data_in.hasOwnProperty(chartName + '_chart'))) {
                return false;
            };
            var chartConfig = {
                type: 'line',
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
                                display: false,
                                labelString: ''
                            }
                        }]
                    }
                }
            };
            var chartCanvas = document.getElementById(chartName + '_chart');
            chartCanvas = this.resetCanvas(chartCanvas);
            var ctx = chartCanvas.getContext('2d');
            new ChartJs(ctx, chartConfig);
        },
        parseNameFromAliases: function (alias, alias_type, data) {
            var name = alias;
            var choices = [];
            var index = 0;
            if (alias_type === 'cons_status') {
                choices = this.flatten_arr(data['iucn_name_list']);
            }
            if (alias_type === 'origin') {
                choices = this.flatten_arr(data['origin_name_list']);
            }
            if (choices.length > 0) {
                index = choices.indexOf(alias) + 1;
                name = choices[index];
            }
            return name;
        },
        showDetail: function (name, zoomToObject) {
            var self = this;
            // Render basic information
            var $siteDetailWrapper = $('<div></div>');
            $siteDetailWrapper.append(
                '<div id="site-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> Site Details </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $siteDetailWrapper.append(
                '<div id="biodiversity-data" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> Biodiversity Data </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            $siteDetailWrapper.append(
                '<div id="climate-data" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> Climate Data </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $siteDetailWrapper);
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', '<i class="fa fa-map-marker"></i> Loading...');
            $siteDetailWrapper.find('.search-results-total').click(self.hideAll);
            $siteDetailWrapper.find('.search-results-total').click();

            // call detail
            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }
            Shared.LocationSiteDetailXHRRequest = $.get({
                url: this.url,
                dataType: 'json',
                success: function (data) {
                    self.siteDetailData = data;
                    Shared.Dispatcher.trigger('sidePanel:updateSiteDetailData', self.siteDetailData);
                    if (data['geometry']) {
                        var feature = {
                            id: data['id'],
                            type: "Feature",
                            geometry: JSON.parse(data['geometry']),
                            properties: {}
                        };
                        var features = new ol.format.GeoJSON().readFeatures(feature, {
                            featureProjection: 'EPSG:3857'
                        });
                        if (zoomToObject) {
                            Shared.Dispatcher.trigger('map:switchHighlight', features, !zoomToObject);
                        } else {
                            Shared.Dispatcher.trigger('map:switchHighlight', features, true);
                        }
                    }
                    let sidePanelTitle = '<i class="fa fa-map-marker"></i> ' + data['site_detail_info']['fbis_site_code'];
                    if (isStaff) {
                        sidePanelTitle += '<a href="/admin/bims/locationsite/' + data['id'] + '/change/" style="float: right; padding-top: 5px">Edit</a>';
                    }
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', sidePanelTitle);

                    // render site detail
                    $('#site-detail').append(self.renderSiteDetailInfo(data));
                    self.renderBiodiversityDataSection($('#biodiversity-data'), data);
                    self.renderCharts();
                    self.renderLegends(self.originLegends, $('.origin-legends'));
                    self.renderLegends(self.endemismLegends, $('.endemism-legends'));
                    self.renderLegends(self.consStatusLegends, $('.cons-status-legends'));

                    let climateDataHTML = self.renderClimateData(data);
                    $('#climate-data').append(climateDataHTML);
                    self.renderMonthlyLineChart(data['climate_data'], 'temperature');
                    self.renderMonthlyLineChart(data['climate_data'], 'rainfall');

                    Shared.LocationSiteDetailXHRRequest = null;
                },
                error: function (req, err) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelHtml', {});
                },
            });
        },
        renderBiodiversityDataSection: function (container, data) {
            let self = this;

            let $sectionContainer = $('<div class="container-fluid"></div>');
            container.append($sectionContainer);

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
            let $sassDashboarRow = $('<tr></tr>');
            let $formRow = $('<tr></tr>');
            $table.append($iconHead);
            $table.append($occurrenceRow);
            $table.append($siteRow);
            $table.append($originRow);
            $table.append($endemismRow);
            $table.append($consStatusRow);
            $table.append($numTaxaRow);
            $table.append($dashboardRow);
            $table.append($formRow);
            $table.append($sassDashboarRow);

            $iconHead.append('<td></td>');
            $occurrenceRow.append('<td>Occurrences</td>');
            $originRow.append('<td>Origin<div class="origin-legends"></div></td>');
            $endemismRow.append('<td>Endemism<div class="endemism-legends"></div></td>');
            $consStatusRow.append('<td>Cons. Status<div class="cons-status-legends"></div></td>');
            $numTaxaRow.append('<td>Number of Taxa</td>');
            $dashboardRow.append('<td style="padding-top: 12px;">Dashboard</td>');
            $formRow.append('<td style="padding-top: 12px;">Form</td>');

            let $sassDashboardButton = $('<button class="fbis-button-small" style="width: 100%;">SASS Dashboard</button>');
            let $sassDashboardButtonContainer = $('<td colspan="' + (Object.keys(data['biodiversity_data']).length + 1) + '">');
            $sassDashboarRow.append($sassDashboardButtonContainer);
            $sassDashboardButtonContainer.append($sassDashboardButton);
            if (data['sass_exist']) {
                $sassDashboardButton.click(function () {
                    let sassUrl = '/sass/dashboard/' + self.siteId + '/';
                    sassUrl += self.apiParameters(filterParameters);
                    window.location.href = sassUrl;
                });
            } else {
                $sassDashboardButton.addClass('disabled');
            }

            $.each(data['biodiversity_data'], function (key, value) {
                $iconHead.append('<td class="overview-data"><img width="30" src="/uploaded/' + value['icon'] + '"></td></td>');
                $occurrenceRow.append('<td class="overview-data">' + value['occurrences'] + '</td>');
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

                // Form button
                let buttonName = key;
                if (buttonName.toLowerCase().includes('invert')) {
                    buttonName = 'SASS';
                }
                let $formButton = $('<button class="fbis-button-small fbis-red" style="width: 100%"> <span>Add ' + buttonName + '</span> </button>');
                let $formRowContainer = $('<td>');
                $formRowContainer.append($formButton);
                $formRow.append($formRowContainer);
                if (buttonName.toLowerCase() !== 'sass' && buttonName.toLowerCase() !== 'fish') {
                    $formButton.addClass('disabled');
                } else {
                    $formButton.click(function () {
                        let url = '#';
                        if (buttonName.toLowerCase() === 'fish') {
                            url = '/fish-form/?siteId=' + self.siteId;
                        } else if (buttonName.toLowerCase() === 'sass') {
                            url = '/sass/' + self.siteId;
                        }
                        window.location = url;
                    });
                }

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
        flatten_arr: function (arr) {
            let self = this;
            return arr.reduce(function (flat, toFlatten) {
                return flat.concat(Array.isArray(toFlatten) ? self.flatten_arr(toFlatten) : toFlatten);
            }, []);
        },
        renderCharts: function () {
            let self = this;
            $.each(this.charts, function (index, chart) {
                if (chart['data'].length > 0) {
                    self.createPieChart(chart);
                }
            })
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
        renderLegends: function (legends, container) {
            $.each(legends, function (key, value) {
                container.append('<div><span style="color:' +
                    value + ';">■</span>' +
                    '<span style="font-style: italic;">' +
                    key + '</span></div>');
            });
        },
    })
});
