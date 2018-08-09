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
            this.yearFrom = parameters['yearFrom'];
            this.yearTo = parameters['yearTo'];
            this.months = parameters['months'];

            this.url = this.searchUrl +
                '?search=' + this.searchValue +
                '&collector=' + this.collectorValue +
                '&category=' + this.categoryValue +
                '&yearFrom=' + this.yearFrom +
                '&yearTo=' + this.yearTo +
                '&months=' + this.months;
            this.sidePanel = sidePanel;
            this.sidePanel.showSearchLoading();
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
            var result = response['records'];
            result = result.concat(response['sites']);
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
                if (searchResultView.getResultType() == 'taxa') {
                    biologicalCount += searchResultView.model.attributes.count;
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
