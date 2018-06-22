define(['jquery', 'backbone', 'models/search_result', 'views/search_result'], function ($, Backbone, SearchModel, SearchResultView) {
    return Backbone.Collection.extend({
        model: SearchModel,
        url: "",
        searchUrl: "/api/search/",
        viewCollection: [],
        sidePanel: null,
        searchValue: '',
        search: function (searchValue, sidePanel) {
            this.searchValue = searchValue;
            this.url = this.searchUrl + searchValue;
            this.sidePanel = sidePanel;
        },
        hideAll: function (e) {
            if($(e.target).data('visibility')) {
                $(e.target).nextAll().hide();
                $(e.target).data('visibility', false)
            } else {
                $(e.target).nextAll().show();
                $(e.target).data('visibility', true)
            }

        },
        renderCollection: function () {
            var self = this;
            this.sidePanel.updateSidePanelTitle(this.searchValue);

            if(this.models.length === 1) {
                if(this.models[0]['attributes'].hasOwnProperty('results')) {
                    self.sidePanel.fillSidePanelHtml(this.models[0]['attributes']['results']);
                    return false;
                }
            }

            var $searchResultsWrapper = $('<div class="search-results-wrapper"></div>');
            $searchResultsWrapper.append('<div class="search-results-total" data-visibility="true"> Biological Collection Records (' + this.models.length + ') <i class="fa fa-angle-down"></i></div>');

            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];

            $.each(this.models, function (index, model) {
                var searchResultView = new SearchResultView({
                    model: model
                });
                $searchResultsWrapper.append(searchResultView.el);

                self.viewCollection.push(searchResultView);
            });
            self.sidePanel.fillSidePanelHtml($searchResultsWrapper);
            $searchResultsWrapper.find('.search-results-total').click(self.hideAll);
        }
    })
});
