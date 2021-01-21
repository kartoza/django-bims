define(['backbone', 'ol', 'shared', 'chartJs', 'jquery'], function (Backbone, ol, Shared, ChartJs, $) {
    return Backbone.View.extend({
        id: 0,
        currentSpeciesSearchResult: [],
        siteChartData: {},
        siteId: null,
        siteName: null,
        siteDetailData: null,
        features: null,
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
            Shared.Dispatcher.on('siteDetail:panelClosed', this.panelClosed, this);
            Shared.Dispatcher.on('siteDetail:updateCurrentSpeciesSearchResult', this.updateCurrentSpeciesSearchResult, this);
        },
        updateCurrentSpeciesSearchResult: function (newList) {
            this.currentSpeciesSearchResult = newList;
        },
        show: function (id, name, zoomToObject, addMarker) {
            this.originLegends = {};
            this.endemismLegends = {};
            this.consStatusLegends = {};
            this.siteId = id;
            this.siteName = name;
            this.zoomToObject = zoomToObject;
            if (typeof addMarker === 'undefined' || addMarker === null) {
                this.addMarker = false;
            }
            this.parameters = filterParameters;
            this.parameters['siteId'] = id;
            filterParameters = $.extend(true, {}, this.parameters);
            this.url = '/api/location-site-detail/' + this.apiParameters(this.parameters);
            this.showDetail(name, zoomToObject)
        },
        panelClosed: function (e) {
            // function that is called when the panel closed
            if (!Shared.CurrentState.SEARCH) {
                Shared.Router.updateUrl('', false);
            } else {
                filterParameters['siteIdOpen'] = '';
            }
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
                    '<span class="species-ssdd-legend-title">&nbsp;' +
                    dataKeys[i] + '</span></div>'
            }
            var element_name = `#rp-${chartName}-legend`;
            $(element_name).html(chart_labels[chartName]);
        },
        renderSiteDetailInfo: function (data) {
            var $detailWrapper = $('<div></div>');
            if (data.hasOwnProperty('site_detail_info')) {
                let siteDetailsTemplate = _.template($('#site-details-template').html());
                $detailWrapper.append(siteDetailsTemplate(data));
            }
            return $detailWrapper;
        },
        renderClimateData: function (data) {
            let $detailWrapper = $('<div></div>');
            if (data.hasOwnProperty('climate_data')) {
                let climateDataTemplate = _.template($('#climate-data-template').html());
                $detailWrapper.append(climateDataTemplate({
                    'mean_annual_temperature': data['climate_data']['mean_annual_temperature'],
                    'mean_annual_rainfall': data['climate_data']['mean_annual_rainfall']
                }));
            }
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
            }
            let chartConfig = {
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
                                display: true,
                                labelString: '(mm)'
                            }
                        }]
                    }
                }
            };
            let chartCanvas = document.getElementById(chartName + '_chart');
            chartCanvas = this.resetCanvas(chartCanvas);
            let ctx = chartCanvas.getContext('2d');
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

                    if (Shared.CurrentState.SEARCH) {
                        filterParameters['siteIdOpen'] = data['id'];
                    }
                    let updatedUrl = Shared.UrlUtil.updateUrlParams(window.location.href, 'site', 'siteIdOpen', data['id']);
                    if (updatedUrl) {
                        Shared.Router.updateUrl(updatedUrl, false);
                    }

                    if (data['geometry']) {
                        let feature = {
                            id: data['id'],
                            type: "Feature",
                            geometry: JSON.parse(data['geometry']),
                            properties: {}
                        };
                        let features = new ol.format.GeoJSON().readFeatures(feature, {
                            featureProjection: 'EPSG:3857'
                        });

                        // Show marker
                        if (zoomToObject) {
                            Shared.Dispatcher.trigger('map:switchHighlight', features, !zoomToObject);
                        } else {
                            Shared.Dispatcher.trigger('map:switchHighlight', features, true);
                        }
                    }
                    let sidePanelTitle = '<i class="fa fa-map-marker"></i> ' + data['site_detail_info']['site_code'];
                    if (isStaff || ( userID !== null && userID === data['owner']) ) {
                        sidePanelTitle += '<a href="/location-site-form/update/?id=' + data['id'] + '" style="float: right; padding-top: 5px">Edit</a>';
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

                    // Features other than default site data exist, show the feature info
                    let siteCoordinates = data['site_detail_info']['site_coordinates'].split(',');
                    let lon = siteCoordinates[0].trim();
                    let lat = siteCoordinates[1].trim();
                    Shared.Dispatcher.trigger('layers:showFeatureInfo', lon, lat, true);
                },
                error: function (req, err) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelHtml', {});
                },
            });
        },
        renderBiodiversityDataSection: function (container, data) {
            let self = this;
            let biodiversitySectionTemplate = _.template($('#biodiversity-data-template-new').html());
            container.append(biodiversitySectionTemplate({ data: data.biodiversity_data, is_sass_enabled: is_sass_enabled, sass_exist: data.sass_exist }));
            $.each(data['biodiversity_data'], function (key, value) {
                self.charts.push({
                    'canvas': $("#origin-chart-" + value.module),
                    'data': value['origin'],
                    'legends': self.originLegends
                });
                self.charts.push({
                    'canvas': $("#endemism-chart-" + value.module),
                    'data': value['endemism'],
                    'legends': self.endemismLegends
                });
                self.charts.push({
                    'canvas': $("#cons-chart-" + value.module),
                    'data': value['cons_status'],
                    'legends': self.consStatusLegends
                });
            });
            $('.sp-open-dashboard').click(function (e) {
                let parameters = $.extend(true, {}, filterParameters);
                parameters['modules'] = $(e.target).data('module');
                Shared.Router.updateUrl('site-detail/' + self.apiParameters(parameters).substr(1), true);
            });
            $('.sp-add-record').click(function (e) {
                let url = '#';
                const moduleId = $(e.target).data('module-id');
                const moduleName = $(e.target).data('module-name');
                if (moduleName.toLowerCase() === 'fish') {
                    url = '/fish-form/?siteId=' + self.siteId;
                } else if (moduleName.toLowerCase() === 'invertebrates') {
                    url = '/invert-form/?siteId=' + self.siteId;
                } else if (moduleName.toLowerCase() === 'algae') {
                    url = '/algae-form/?siteId=' + self.siteId;
                } else {
                    url = `/module-form/?siteId=${self.siteId}&module=${moduleId}`;
                }
                window.location = url;
            });
            $('.sp-sass-dashboard').click(function () {
                let sassUrl = '/sass/dashboard/' + self.siteId + '/';
                sassUrl += self.apiParameters(filterParameters);
                window.location.href = sassUrl;
            });
            $('.sp-add-sass').click(function () {
                window.location.href = '/sass/' + self.siteId;
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
