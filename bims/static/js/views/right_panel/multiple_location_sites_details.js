define(['backbone', 'shared', 'chartJs', 'jquery', 'underscore', 'utils/filter_list'], function (Backbone, Shared, ChartJs, $, _, filterList) {
    return Backbone.View.extend({
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        initialize: function () {
            Shared.Dispatcher.on('multiSiteDetailPanel:show', this.show, this);
        },
        show: function () {
            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', '<i class="fa fa-map-marker"></i> Loading...');
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
            let $filterDetailTableContainer = $('<div class="container-fluid" style="padding: 10px;"></div>');
            $filterDetailTableContainer.append($filterDetailTable);
            $filterDetailWrapper.append($filterDetailTableContainer);
            renderFilterList($filterDetailTable);
        },
        renderBiodiversityDataSection: function (container) {
            let $sectionWrapper = $(
                '<div id="biodiversity-data" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> ' +
                '<span class="search-result-title"> Biodiversity Data </span> ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            container.append($sectionWrapper);

        },
        renderPanel: function () {
            let $siteDetailWrapper = $('<div>');
            this.renderFilterHistorySection($siteDetailWrapper);
            this.renderBiodiversityDataSection($siteDetailWrapper);

            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', '<i class="fa fa-map-marker"></i> Multi-Site Overview');
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $siteDetailWrapper);
            $siteDetailWrapper.find('.search-results-total').click(this.hideAll);
            $siteDetailWrapper.find('.search-results-total').click();
        },
        fetchData: function () {
            let self = this;
            setTimeout(function () {
                self.renderPanel();
            }, 1000);
        }
    });
});
