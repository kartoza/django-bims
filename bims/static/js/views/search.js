define(['backbone', 'underscore', 'shared', 'ol', 'collections/search_result'], function (Backbone, _, Shared, ol, SearchResultCollection) {

    return Backbone.View.extend({
        template: _.template($('#map-search-container').html()),
        searchBox: null,
        searchBoxOpen: false,
        searchResults: {},
        events: {
            'keypress #search': 'searchEnter',
            'click .search-arrow': 'searchClick'
        },
        search: function () {
            var self = this;
            this.sidePanel.openSidePanel();
            this.sidePanel.clearSidePanel();

            $('#search-results-wrapper').html('');
            var searchValue = $('#search').val();
            if (searchValue.length < 3) {
                this.sidePanel.fillSidePanelHtml("<div id='search-results-container'>Minimal 3 characters</div>");
                return false;
            }

            var collectorValue = [];
            $('input[name=collector-value]:checked').each(function () {
                collectorValue.push($(this).val())
            });
            if (collectorValue.length === 0) {
                collectorValue = null
            } else {
                collectorValue = JSON.stringify(collectorValue)
            }

            var categoryValue = [];
            $('input[name=category-value]:checked').each(function () {
                categoryValue.push($(this).val())
            });
            if (categoryValue.length === 0) {
                categoryValue = null
            } else {
                categoryValue = JSON.stringify(categoryValue)
            }

            this.searchResultCollection.search(
                searchValue,
                this.sidePanel,
                collectorValue,
                categoryValue,
                this.datePickerToDate($('#date-filter-from')),
                this.datePickerToDate($('#date-filter-to'))
            );
            this.searchResultCollection.fetch({
                success: function () {
                    self.searchResultCollection.renderCollection()
                }
            });
        },
        searchClick: function () {
            this.search();
        },
        searchEnter: function (e) {
            if (e.which === 13) {
                this.search();
            }
        },
        datePickerToDate: function (element) {
            if ($(element).val()) {
                return new Date($(element).val().replace(/(\d{2})-(\d{2})-(\d{4})/, "$2/$1/$3")).getTime()
            } else {
                return '';
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