
define(['backbone', 'underscore', 'shared', 'ol', 'collections/search_result'], function (Backbone, _, Shared, ol, SearchResultCollection) {

    return Backbone.View.extend({
        template: _.template($('#map-search-container').html()),
        searchBox: null,
        searchBoxOpen: false,
        searchResults: {},
        events: {
            'keypress #search': 'searchEnter',
            'click .result-search': 'searchResultClicked',
        },
        searchEnter: function (e) {
            var self = this;
            if(e.which === 13) {
                var $searchResultsContainer = $("<div id='search-results-container'></div>");
                this.sidePanel.openSidePanel();

                $('#search-results-wrapper').html('');
                var searchValue = $(e.target).val();
                if(searchValue.length < 3) {
                    $searchResultsContainer.html('Minimal 3 characters');
                    Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $searchResultsContainer.html());
                    return false;
                }

                this.searchResultCollection.search(searchValue, this.sidePanel);
                this.searchResultCollection.fetch({
                    success: function () {
                        self.searchResultCollection.renderCollection()
                    }
                });
            }
        },
        searchResultClicked: function (e) {
            var id = $(e.target).data('search-result-id');
            if(typeof id === "undefined") {
                return false;
            }

            var searchResult = this.searchResults[id];
            var geometry = JSON.parse(searchResult['geometry']);
            var coordinates = ol.proj.transform(geometry['coordinates'], "EPSG:4326", "EPSG:3857");
            var zoomLevel = 15;
            Shared.Dispatcher.trigger('map:zoomToCoordinates', coordinates, zoomLevel);

        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.sidePanel = options.sidePanel;
            this.searchResultCollection = new SearchResultCollection();
        },
        render: function () {
            this.$el.html(this.template());
            this.searchBox = this.$el.find('.map-search-box');
            this.searchBox.hide();
            return this;
        },
        show: function () {
            this.searchBox.show();
            this.$el.find('#search').focus();
            this.searchBoxOpen = true;
        },
        hide: function () {
            this.searchBox.hide();
            this.searchBoxOpen = false;
        },
        isOpen: function () {
            return this.searchBoxOpen;
        }
    })

});