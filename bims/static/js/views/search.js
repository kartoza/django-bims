
define(['backbone', 'underscore', 'shared', 'ol', 'collections/search_result'], function (Backbone, _, Shared, ol, SearchResultCollection) {

    return Backbone.View.extend({
        template: _.template($('#map-search-container').html()),
        searchBox: null,
        searchBoxOpen: false,
        searchResults: {},
        events: {
            'keypress #search': 'searchEnter'
        },
        searchEnter: function (e) {
            var self = this;
            if(e.which === 13) {
                this.sidePanel.openSidePanel();
                this.sidePanel.clearSidePanel();

                $('#search-results-wrapper').html('');
                var searchValue = $(e.target).val();
                if(searchValue.length < 3) {
                    this.sidePanel.fillSidePanelHtml("<div id='search-results-container'>Minimal 3 characters</div>");
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