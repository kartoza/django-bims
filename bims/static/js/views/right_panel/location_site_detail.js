define(['backbone', 'ol', 'shared', 'chartJs', 'jquery'], function (Backbone, ol, Shared, ChartJs, $) {
    return Backbone.View.extend({
        id: 0,
        currentSpeciesSearchResult: [],
        siteChartData: {},
        siteId: null,
        siteName: null,
        siteDetailData: null,
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
        initialize: function () {
            Shared.Dispatcher.on('siteDetail:show', this.show, this);
            Shared.Dispatcher.on('siteDetail:updateCurrentSpeciesSearchResult', this.updateCurrentSpeciesSearchResult, this);
        },
        updateCurrentSpeciesSearchResult: function (newList) {
            this.currentSpeciesSearchResult = newList;
        },
        show: function (id, name, zoomToObject) {
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
        renderSiteDetail: function (data) {
            var $detailWrapper = $('<div></div>');
            var locationContext = {};
            var maxPanelThatShouldBeOpen = 1;
            var self = this;

            if (data.hasOwnProperty('location_context_document_json')) {
                locationContext = data['location_context_document_json'];
            }
            if (locationContext.hasOwnProperty('context_group_values')) {
                 var contextGroups = locationContext['context_group_values'];
                 $.each(contextGroups, function (index, value) {
                     var $classWrapper = $('<div class="sub-species-wrapper"></div>');

                     var subPanel = _.template($('#site-detail-sub-title').html());
                     var siteDetailTemplate = _.template($('#site-detail-registry-values').html());
                     $classWrapper.append(subPanel({
                         name: value['name']
                     }));

                     if (!value.hasOwnProperty('service_registry_values')) {
                         return true;
                     }

                     if (value['service_registry_values'].length === 0) {
                         return true;
                     }

                     // TODO : Change this to check graphable value
                     var isChart = value['name'].toLowerCase().includes('monthly') | value['service_registry_values'][0]['key'].includes('monthly');
                     var chartData = [];

                     $.each(value['service_registry_values'], function (service_index, service_value) {
                         if (!service_value.hasOwnProperty('name') ||
                             !service_value.hasOwnProperty('value')) {
                                return true;
                         }

                         var service_value_name = service_value['name'];
                         var service_value_value = service_value['value'];

                         if (!service_value_name || !service_value_value) {
                             return true;
                         }

                         // If this is chart data, put the data to dictionary
                         if (isChart) {
                             var date = '';
                             $.each(self.months, function (key, value) {
                                if (service_value_name.toLowerCase().includes(key)) {
                                    date = value;
                                }
                             });
                             if (!date) {
                                 return true;
                             }
                             chartData.push(
                                 {
                                     'name': date,
                                     'value': service_value_value
                                 }
                             );
                             return true;
                         }

                        $classWrapper.append(
                            siteDetailTemplate({
                                name: service_value_name,
                                value: service_value_value
                            })
                        );
                     });

                     $detailWrapper.append($classWrapper);
                     var $wrapperTitleDiv = $classWrapper.find('.search-result-sub-title');
                     $wrapperTitleDiv.click(function (e) {
                        $(this).parent().find('.result-search').toggle();
                     });

                     // Create canvas for chart, will create chart later after div ready
                     if (chartData.length > 0) {
                         var canvasKey = value['key'];

                         var resultSarch = $('<div class="result-search result-chart"></div>');
                         $('<canvas>').attr({
                             id: canvasKey
                         }).css({
                             width: '250px',
                             height: '145px'
                         }).appendTo(resultSarch);

                         $classWrapper.append(resultSarch);
                         self.siteChartData[canvasKey] = chartData;
                     }

                     if (index > maxPanelThatShouldBeOpen - 1) {
                         $classWrapper.find('.result-search').hide();
                     }

                 })
            } else {
                $detailWrapper.append('<div class="side-panel-content">No detail for this site.</div>');
            }

            // Add detail dashboard button
            var button = `
                <div class="container-fluid">
                <button class="btn fbis-button right-panel-button 
                               open-detailed-site-button">Dashboard</button>`;
            $detailWrapper.append(button);

            if (is_sass_enabled) {
                var sassButton = `
                    <div class="container-fluid"><a 
                    href="/sass/${this.parameters['siteId']}
                    " class="btn right-panel-button right-panel-last-button 
                             fbis-button sass-button">SASS +</a></div>`;
                $detailWrapper.append(sassButton);
            }

            return $detailWrapper;
        },
        renderDashboardDetail: function (data) {
            var $detailWrapper = $('<div></div>');

            if (!data.hasOwnProperty('records_occurrence')) {
                $detailWrapper.append('<div class="side-panel-content">' +
                    'No detail for this site.' +
                    '</div>');
                return $detailWrapper;
            }

            var recordsOccurence = data['records_occurrence'];
            var originTemplate = _.template($('#search-result-dashboard-origin-template').html());
            var richnessIndexTemplate = _.template($('#search-result-dashboard-richness-index-template').html());
            var classes = Object.keys(recordsOccurence).sort();

            if (recordsOccurence.length === 0) {
                 $detailWrapper.append('<div class="side-panel-content">' +
                    'No detail for this site.' +
                    '</div>');
                return $detailWrapper;
            }

            var totalSpeciesRichness = 0;

            $.each(classes, function (index, className) {
                var record = recordsOccurence[className];
                if (!className) {
                    className = 'Unknown Class';
                }
                var $classWrapper = $('<div class="sub-species-wrapper"></div>');

                var classTemplate = _.template($('#search-result-sub-title').html());
                $classWrapper.append(classTemplate({
                    name: className,
                    count: 0,
                }));

                var species = Object.keys(record).sort();
                var totalRecords = 0;
                var category = {
                    'alien': 0,
                    'indigenous': 0,
                    'translocated': 0
                };

                $.each(species, function (index, speciesName) {
                    var speciesValue = record[speciesName];
                    var $occurencesIndicator = $classWrapper.find('.total-occurences');
                    totalRecords += speciesValue.count;
                    $occurencesIndicator.html(
                        parseInt($occurencesIndicator.html()) + speciesValue.count);
                    category[speciesValue['category']] += 1;
                });

                // Origin
                $classWrapper.append(originTemplate({
                    name: 'Origin',
                    nativeValue: category['indigenous'] / totalRecords * 100,
                    nonNativeValue: category['alien'] / totalRecords * 100,
                    translocatedValue: category['translocated'] / totalRecords * 100
                }));

                // Calculate species richness
                var speciesRichness = species.length / Math.sqrt(totalRecords);
                totalSpeciesRichness += speciesRichness;

                // Calculate shanon diversity and simpson diversity
                var totalShanonDiversity = 0;
                var totalNSimpsonDiversity = 0;

                $.each(species, function (index, speciesName) {

                    // Shanon diversity
                    var speciesValue = record[speciesName];
                    var p = speciesValue.count / totalRecords;
                    var logP = Math.log(p);
                    totalShanonDiversity += -(p * logP);

                    // Simpson diversity
                    totalNSimpsonDiversity += speciesValue.count * (speciesValue.count - 1);
                });

                var simpsonDiversityIndex = 1 - (totalNSimpsonDiversity / (totalRecords * (totalRecords-1)));
                if (isNaN(simpsonDiversityIndex)) {
                    simpsonDiversityIndex = 0;
                }

                // Richness Index
                $classWrapper.append(richnessIndexTemplate({
                    name: 'Richness Index',
                    className: className,
                    speciesRichness: speciesRichness.toFixed(2),
                    shanonDiversity: totalShanonDiversity.toFixed(2),
                    simpsonDiversity: simpsonDiversityIndex.toFixed(2)
                }));

                $detailWrapper.append($classWrapper);

                // Add click event
                var $wrapperTitleDiv = $classWrapper.find('.search-result-sub-title');

                $wrapperTitleDiv.click(function (e) {
                    $(this).parent().find('.result-search').toggle();
                });
            });

            return $detailWrapper;
        },
        renderSpeciesList: function (data) {
            var that = this;
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
                        count: 0
                    }));
                    $classWrapper.hide();

                    var species = Object.keys(value).sort();
                    $.each(species, function (index, speciesName) {
                        if (that.currentSpeciesSearchResult.length > 0) {
                            // check if species name is on search mode
                            if ($.inArray(speciesName, that.currentSpeciesSearchResult) < 0) {
                                return true;
                            }
                        }
                        var speciesValue = value[speciesName];
                        $classWrapper.append(
                            template({
                                common_name: speciesName,
                                count: speciesValue.count,
                                taxon_gbif_id: speciesValue.taxon_id
                            })
                        );

                        // Species clicked
                        $classWrapper.find('#'+speciesValue.taxon_id).click(function (e) {
                            e.preventDefault();
                            Shared.Dispatcher.trigger('taxonDetail:show',
                                speciesValue.taxon_id,
                                speciesName,
                                {
                                    'id': that.siteId,
                                    'name': that.siteName
                                },
                                speciesValue.count
                            );
                        });

                        var $occurencesIndicator = $classWrapper.find('.total-occurences');
                        $occurencesIndicator.html(parseInt($occurencesIndicator.html()) + speciesValue.count);
                        $classWrapper.show();
                        speciesListCount += 1;
                    });
                    $specialListWrapper.append($classWrapper);
                    var $wrapperTitleDiv = $classWrapper.find('.search-result-sub-title');
                    $wrapperTitleDiv.click(function (e) {
                        $(this).parent().find('.result-search').toggle();
                    });
                });
            } else {
                $specialListWrapper.append('<div class="side-panel-content">No species found on this site.</div>');
            }
            $('.species-list-count').html(speciesListCount);
            return $specialListWrapper;
        },

        showDetail: function (name, zoomToObject) {
            var self = this;
            // Render basic information
            var $siteDetailWrapper = $('<div></div>');
            $siteDetailWrapper.append(
                '<div id="dashboard-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> DASHBOARD </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $siteDetailWrapper.append(
                '<div id="site-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> SITE DETAILS </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            $siteDetailWrapper.append(
                '<div id="species-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> ' +
                '<span class="search-result-title"> SPECIES LIST (<span class="species-list-count"><i>loading</i></span>) ' +
                '</span> <i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

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
                    // render site detail
                    $('#site-detail').append(self.renderSiteDetail(data));
                    $.each(self.siteChartData, function (key, value) {
                        var chartConfig = {
                            type: 'line',
                            data: {
                                labels: [],
                                datasets: [{
                                    backgroundColor: '#ddd14e',
                                    borderColor: '#ddd14e',
                                    data: [],
                                    fill: false
                                }]
                            },
                            options: {
                                responsive: true,
                                legend: { display: false },
                                title: { display: false },
                                hover: { mode: 'nearest', intersect: false},
                                scales: {
                                    xAxes: [{
                                        display: true,
                                        scaleLabel: {
                                            display: true,
                                            labelString: 'Month'
                                        }
                                    }],
                                    yAxes: [{
                                        display: true,
                                        scaleLabel: {
                                            display: false
                                        }
                                    }]
                                }
                            }
                        };
                        var canvas = document.getElementById(key);
                        var ctx = canvas.getContext('2d');
                        var labels = [];
                        var chartData = [];
                        $.each(value, function (index, record_value) {
                           labels.push(record_value['name']);
                           chartData.push(Number(record_value['value']).toFixed(2));
                        });
                        chartConfig['data']['labels'] = labels;
                        chartConfig['data']['datasets'][0]['data'] = chartData;
                        new ChartJs(ctx, chartConfig);
                    });

                    self.siteChartData = {};

                    // dashboard detail
                    try {
                        // Custom dashboard
                        $('#dashboard-detail').append(renderDashboard(data));
                        calculateChart($('#dashboard-detail'), data);
                    } catch (err) {
                        $('#dashboard-detail').append(self.renderDashboardDetail(data));
                    }

                    // render species list
                    $('#species-list').append(self.renderSpeciesList(data));
                    Shared.LocationSiteDetailXHRRequest = null;
                },
                error: function (req, err) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelHtml', {});
                }
            });
        }
    })
});
