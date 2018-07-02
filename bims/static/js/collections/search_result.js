define(['jquery', 'backbone', 'models/search_result', 'views/search_result'], function ($, Backbone, SearchModel, SearchResultView) {
    return Backbone.Collection.extend({
        model: SearchModel,
        url: "",
        searchUrl: "/api/search/",
        viewCollection: [],
        sidePanel: null,
        searchValue: '',
        search: function (sidePanel, parameters) {
            this.searchValue = parameters['search'];
            this.collectorValue = parameters['collector'];
            this.categoryValue = parameters['category'];
            this.dateFrom = parameters['dateFrom'];
            this.dateTo = parameters['dateTo'];

            this.url = this.searchUrl + this.searchValue +
                '?collector=' + this.collectorValue +
                '&category=' + this.categoryValue +
                '&date-from=' + this.dateFrom +
                '&date-to=' + this.dateTo;
            this.sidePanel = sidePanel;
        },
        hideAll: function (e) {
            if ($(e.target).data('visibility')) {
                $(e.target).nextAll().hide();
                $(e.target).data('visibility', false)
            } else {
                $(e.target).nextAll().show();
                $(e.target).data('visibility', true)
            }

        },
        parse: function (response) {
            var result = response['biological_collection_record'];
            result = result.concat(response['taxa']);
            result = result.concat(response['location_site']);
            return result
        },
        renderCollection: function () {
            var self = this;
            this.sidePanel.updateSidePanelTitle(this.searchValue);
            this.sidePanel.switchToSearchResultPanel();

            if (this.models.length === 1) {
                if (this.models[0]['attributes'].hasOwnProperty('results')) {
                    self.sidePanel.fillSidePanelHtml(this.models[0]['attributes']['results']);
                    return false;
                }
            }

            var $searchResultsWrapper = $('<div></div>');
            $searchResultsWrapper.append(
                '<div id="biological-record-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Biological Collection Records (<span class="number"></span>) </div></div>');
            $searchResultsWrapper.append(
                '<div id="taxa-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Taxa (<span class="number"></span>) </div></div>');
            $searchResultsWrapper.append(
                '<div id="site-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> Location Sites (<span class="number"></span>) </div></div>');

            self.sidePanel.fillSidePanelHtml($searchResultsWrapper);

            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];

            var biologicalCount = 0;
            var taxaCount = 0;
            var siteCount = 0;
            $.each(this.models, function (index, model) {
                var searchResultView = new SearchResultView({
                    model: model
                });
                self.viewCollection.push(searchResultView);

                // update count
                if (searchResultView.getResultType() == 'bio') {
                    biologicalCount += searchResultView.model.attributes.count;
                } else if (searchResultView.getResultType() == 'taxa') {
                    taxaCount += 1;
                } else if (searchResultView.getResultType() == 'site') {
                    siteCount += 1
                }
            });
            $('#biological-record-list .number').html(biologicalCount);
            $('#taxa-list .number').html(taxaCount);
            $('#site-list .number').html(siteCount);
            $searchResultsWrapper.find('.search-results-total').click(self.hideAll);
            $searchResultsWrapper.find('.search-results-total').click();
        }
    })
});
