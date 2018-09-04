define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        currentSpeciesSearchResult: [],
        initialize: function () {
            Shared.Dispatcher.on('siteDetail:show', this.show, this);
            Shared.Dispatcher.on('siteDetail:updateCurrentSpeciesSearchResult', this.updateCurrentSpeciesSearchResult, this);
        },
        updateCurrentSpeciesSearchResult: function (newList) {
            this.currentSpeciesSearchResult = newList;
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
            var locationContext = {};
            var maxPanelThatShouldBeOpen = 1;

            if (data.hasOwnProperty('location_context_document_json')) {
                locationContext = data['location_context_document_json'];
            }
            if (locationContext.hasOwnProperty('context_group_values')) {
                 var contextGroups = locationContext['context_group_values'];
                 $.each(contextGroups, function (index, value) {
                     var $classWrapper = $('<div class="sub-species-wrapper"></div>');

                     $classWrapper.click(function (e) {
                         $(this).find('.result-search').toggle();
                     });

                     var subPanel = _.template($('#site-detail-sub-title').html());
                     var siteDetailTemplate = _.template($('#site-detail-registry-values').html());
                     $classWrapper.append(subPanel({
                         name: value['name']
                     }));

                     if (value.hasOwnProperty('service_registry_values')) {
                         $.each(value['service_registry_values'], function (service_index, service_value) {
                             if (service_value.hasOwnProperty('name') &&
                                 service_value.hasOwnProperty('value')) {
                                 var service_value_name = service_value['name'];
                                 var service_value_value = service_value['value'];

                                 if (service_value_value &&  service_value_name) {
                                    $classWrapper.append(
                                        siteDetailTemplate({
                                            name: service_value_name,
                                            value: service_value_value
                                        })
                                    );
                                 }
                             }
                         })
                     }

                     $detailWrapper.append($classWrapper);
                     if (index > maxPanelThatShouldBeOpen - 1) {
                         $classWrapper.find('.result-search').hide();
                     }

                 })
            } else {
                $detailWrapper.append('<div class="side-panel-content">No detail for this site.</div>');
            }
            return $detailWrapper;
        },
        renderDashboardDetail: function (data) {
            var $detailWrapper = $('<div></div>');
            if ($('#site-dashboard-template').length == 0) {
                $detailWrapper.append('<div class="side-panel-content">No detail for this site.</div>');
            } else {
                $detailWrapper.append(_.template($('#site-dashboard-template').html()));
            }
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
                                taxon_gbif_id: speciesValue.taxon_gbif_id
                            })
                        );

                        var $occurencesIndicator = $classWrapper.find('.total-occurences');
                        $occurencesIndicator.html(parseInt($occurencesIndicator.html()) + speciesValue.count);
                        $classWrapper.show();
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
                '<div class="search-results-total" data-visibility="false"> Dashboard <i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
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

                    // dashboard detail
                    $('#dashboard-detail').append(self.renderDashboardDetail(data));
                    try {
                        renderDashboard(data);
                    } catch (err) {

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
