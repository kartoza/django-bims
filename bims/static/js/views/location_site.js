define(['backbone', 'models/location_site', 'ol', 'shared'], function (Backbone, LocationSite, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        initialize: function (options) {
            this.render();
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
                $.each(records_occurrence, function (key, value) {
                    if (key) {
                        var $classWrapper = $('<div class="sub-species-wrapper"></div>');
                        var classTemplate = _.template($('#search-result-sub-title').html());
                        $classWrapper.append(classTemplate({
                            name: key,
                            count: Object.keys(value).length
                        }));
                        $.each(value, function (species, speciesValue) {
                            $classWrapper.append(
                                template(speciesValue)
                            );
                            speciesListCount += 1;
                        });
                        $specialListWrapper.append($classWrapper);
                    }
                });
            } else {
                $specialListWrapper.append('<div class="side-panel-content">No species found on this site.</div>');
            }
            $('.species-list-count').html(speciesListCount);
            return $specialListWrapper;
        },
        clicked: function () {
            var self = this;
            var properties = this.model.attributes['properties'];
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
                '<div class="search-results-total" data-visibility="true"> Species List (<span class="species-list-count"></span>)<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $siteDetailWrapper.append(
                '<div id="resources-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Resources <i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', properties);
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $siteDetailWrapper);
            $siteDetailWrapper.find('.search-results-total').click(self.hideAll);
            $siteDetailWrapper.find('.search-results-total').click();

            // call detail
            if (Shared.LocationSiteDetailXHRRequest) {
                Shared.LocationSiteDetailXHRRequest.abort();
                Shared.LocationSiteDetailXHRRequest = null;
            }
            Shared.LocationSiteDetailXHRRequest = $.get({
                url: this.model.url,
                dataType: 'json',
                success: function (data) {
                    // render site detail
                    var siteDetailHtml = self.renderSiteDetail(data);
                    $('#site-detail').append(siteDetailHtml);

                    // render species list
                    var $specialListWrapper = self.renderSpeciesList(data);
                    $('#species-list').append($specialListWrapper);
                    $specialListWrapper.find('.result-search').click(function (e) {
                        var $element = $(e.target);
                        var taxonID = $(e.target).data('taxon-id');
                        if (!taxonID) {
                            $element = $(e.target).closest('.result-search');
                            taxonID = $element.data('taxon-id');
                        }
                        Shared.Dispatcher.trigger(
                            'searchResult:updateTaxon',
                            taxonID,
                            $element.find('.group-title').html()
                        );
                    });

                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelHtml', {});
                    Shared.LocationSiteDetailXHRRequest = null;
                },
                error: function (req, err) {
                    Shared.Dispatcher.trigger('sidePanel:updateSidePanelHtml', {});
                }
            });
        },
        render: function () {
            var modelJson = this.model.toJSON();
            var properties = this.model.attributes['properties'];
            this.id = this.model.attributes['properties']['id'];
            this.model.set('id', this.id)
            if (!this.model.attributes['properties']['count']) {
                Shared.Dispatcher.on('locationSite-' + this.id + ':clicked', this.clicked, this);
            }
            this.features = new ol.format.GeoJSON().readFeatures(modelJson, {
                featureProjection: 'EPSG:3857'
            });
            Shared.Dispatcher.trigger('map:addBiodiversityFeatures', this.features)
        },
        destroy: function () {
            Shared.Dispatcher.unbind('locationSite-' + this.id + ':clicked');
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
