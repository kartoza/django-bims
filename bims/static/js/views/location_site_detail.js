define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        initialize: function () {
            Shared.Dispatcher.on('siteDetail:show', this.show, this);
        },
        show: function (id, name) {
            this.url = '/api/location-site/' + id;
            this.showDetail(name)
        },
        hideAll: function (e) {
            if ($(e.target).data('visibility')) {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-down');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-up');
                $(e.target).nextAll().hide();
                $(e.target).data('visibility', false)
            } else {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-up');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-down');
                $(e.target).nextAll().show();
                $(e.target).data('visibility', true)
            }
        },
        renderSiteDetail: function (data) {
            var $detailWrapper = $('<div></div>');
            $detailWrapper.append('<div class="side-panel-content">No detail for this site.</div>');
            return $detailWrapper;
        },
        renderSpeciesList: function (data) {
            var $specialListWrapper = $('<div style="display: none"></div>');
            var speciesListCount = 0;
            if (data.hasOwnProperty('records_occurrence')) {
                var records_occurrence = data['records_occurrence'];
                var template = _.template($('#search-result-record-template').html());
                var classes = Object.keys(records_occurrence).sort();
                $.each(classes, function (index, className) {
                    var value = records_occurrence[className];
                    if (!className) {
                        className = 'Unknown';

                    }
                    var $classWrapper = $('<div class="sub-species-wrapper"></div>');
                    var classTemplate = _.template($('#search-result-sub-title').html());
                    $classWrapper.append(classTemplate({
                        name: className,
                        count: Object.keys(value).length
                    }));

                    var species = Object.keys(value).sort();
                    $.each(species, function (index, speciesName) {
                        var speciesValue = value[speciesName];
                        $classWrapper.append(
                            template({
                                common_name: speciesName,
                                count: speciesValue.count,
                                taxon_gbif_id: speciesValue.taxon_gbif_id
                            })
                        );
                        speciesListCount += 1;
                    });
                    $specialListWrapper.append($classWrapper);
                });
            } else {
                $specialListWrapper.append('<div class="side-panel-content">No species found on this site.</div>');
            }
            $('.species-list-count').html(speciesListCount);
            return $specialListWrapper;
        },
        showDetail: function (name) {
            var self = this;
            // Render basic information
            var $siteDetailWrapper = $('<div></div>');
            $siteDetailWrapper.append(
                '<div id="site-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> Site details <i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $siteDetailWrapper.append(
                '<div id="dashboard-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Dashboard <i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $siteDetailWrapper.append(
                '<div id="species-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Species List (<span class="species-list-count"><i>loading</i></span>)<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $siteDetailWrapper.append(
                '<div id="resources-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Resources <i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $siteDetailWrapper);
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', '<i class="fa fa-map-marker"></i> ' + name);
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
                    // render site detail
                    $('#site-detail').append(self.renderSiteDetail(data));

                    // render species list
                    $('#species-list').append(self.renderSpeciesList(data));
                    Shared.LocationSiteDetailXHRRequest = null;
                },
                error: function (req, err) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelHtml', {});
                }
            });

            if(isHealthyrivers) {
                this.renderHealthyriversElement()
            }
        },
        createDataGraph: function (container, data, barType, labels, options, colorOptions) {
            var myChart = new Chart(container, {
                type: barType,
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colorOptions['backgroundColor'],
                        borderColor: colorOptions['borderColor'],
                        borderWidth: 1
                    }]
                },
                options: options
            });
        },
        createPieChart: function (container, data, labels, options, colorOptions) {
            var myPieChart = new Chart(container,{
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
        renderHealthyriversElement: function () {
            $('#healthyrivers-side-panel').show();
            var barOptions = {
                scales: {
                    xAxes: [{
                        gridLines: {
                            display:false
                        },
                        ticks: {
                            autoSkip: false,
                            maxRotation: 90,
                            minRotation: 90,
                            padding: -100,
                            fontColor: '#000000',
                            fontStyle: 'bold',
                        },
                        categoryPercentage: 1,
                        barPercentage: 1,
                    }],
                    yAxes: [{
                        gridLines: {
                            display:false,
                            drawBorder: false
                        },
                        ticks: {
                            display: false
                        }
                    }]
                },
                legend: {
                    display: false
                }
            };

            var barColor = {
                'backgroundColor': [
                        'rgba(222, 210, 65, 0.5)',
                        'rgba(98, 156, 68, 0.5)',
                        'rgba(62, 80, 50, 0.5)'
                    ],
                'borderColor': [
                        'rgba(222, 210, 65,1)',
                        'rgba(98, 156, 68, 1)',
                        'rgba(62, 80, 50, 1)'
                    ]
            };

            var options = {
                layout: {
                    padding: {
                        left: -10,
                        right: 0,
                        top: 0,
                        bottom: 0
                    }
                },
                scales: {
                    yAxes: [{
                        gridLines: {
                            display:false
                        },
                        ticks: {
                            autoSkip: false,
                            padding: -120,
                            fontColor: '#000000',
                            fontStyle: 'bold',
                        },
                        categoryPercentage: 1,
                        barPercentage: 1,
                    }],
                    xAxes: [{
                        gridLines: {
                            display:false,
                            drawBorder: false
                        },
                        ticks: {
                            display: false
                        }
                    }]
                },
                legend: {
                    display: false
                }
            };

            var horizontalBarColor = {
                'backgroundColor': [
                        'rgba(236, 230, 150, 0.5)',
                        'rgba(222, 210, 65, 0.5)',
                        'rgba(242, 237, 182, 0.5)'
                    ],
                'borderColor': [
                        'rgba(0, 0, 0, 1)',
                        'rgba(0, 0, 0, 1)',
                        'rgba(0, 0, 0, 1)'
                    ]
            };

            // Note: data are dummies.
            this.createDataGraph(document.getElementById("fish-graph").getContext('2d'), [12, 19, 3], 'bar', ["Native", "Non-Native", "Translocated"], barOptions, barColor);
            this.createDataGraph(document.getElementById("invertebrates-graph").getContext('2d'), [5, 50, 20], 'bar', ["Native", "Non-Native", "Translocated"], barOptions, barColor);
            this.createDataGraph(document.getElementById("algae-graph").getContext('2d'), [12, 19, 3], 'bar', ["Native", "Non-Native", "Translocated"], barOptions, barColor);
            this.createDataGraph(document.getElementById("fish-calculation-graph").getContext('2d'), [12, 19, 3], 'horizontalBar', ["Species Richness", "Shannon Diversity", "Simpson Diversity"], options, horizontalBarColor);
            this.createDataGraph(document.getElementById("invertebrates-calculation-graph").getContext('2d'), [5, 50, 20], 'horizontalBar', ["Species Richness", "Shannon Diversity", "Simpson Diversity"], options, horizontalBarColor);
            this.createDataGraph(document.getElementById("algae-calculation-graph").getContext('2d'), [12, 19, 3], 'horizontalBar', ["Species Richness", "Shannon Diversity", "Simpson Diversity"], options, horizontalBarColor);

            var pieData = [25, 2, 7, 10, 12, 25, 60];
            var pieLabel = ['grey', 'black', 'red', 'orange', 'yellow', 'lightgreen', 'green'];
            var pieColor = ['grey', 'black', 'red', 'orange', 'yellow', 'lightgreen', 'green'];
            var pieOptions = {
                legend: {
                    display: false
                 },
                cutoutPercentage: 0,
                maintainAspectRatio: false
            };
            this.createPieChart(document.getElementById("fish-pie-chart-major").getContext('2d'), pieData, pieLabel, pieOptions, pieColor);
            this.createPieChart(document.getElementById("invertebrates-pie-chart-major").getContext('2d'), pieData, pieLabel, pieOptions, pieColor);
            this.createPieChart(document.getElementById("algae-pie-chart-major").getContext('2d'), pieData, pieLabel, pieOptions, pieColor);

            var pieData2 = [25, 50, 12, 40, 10];
            var pieLabel2 = ['purple', 'white', 'blue', 'green', 'orange'];
            var pieColor2 = ['purple', 'white', 'blue', 'green', 'orange'];
            this.createPieChart(document.getElementById("fish-pie-chart-minor").getContext('2d'), pieData2, pieLabel2, pieOptions, pieColor2);
            this.createPieChart(document.getElementById("invertebrates-pie-chart-minor").getContext('2d'), pieData2, pieLabel2, pieOptions, pieColor2);
            this.createPieChart(document.getElementById("algae-pie-chart-minor").getContext('2d'), pieData2, pieLabel2, pieOptions, pieColor2);
        }
    })
});
