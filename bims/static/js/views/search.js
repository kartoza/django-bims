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
        search: function (searchValue) {
            var self = this;
            this.sidePanel.openSidePanel();
            this.sidePanel.clearSidePanel();

            $('#search-results-wrapper').html('');

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
            var parameters = {
                'search': searchValue,
                'collector': collectorValue,
                'category': categoryValue,
                'dateFrom': this.datePickerToDate($('#date-filter-from')),
                'dateTo': this.datePickerToDate($('#date-filter-to'))
            };
            Shared.Dispatcher.trigger('map:closeHighlight');
            Shared.Dispatcher.trigger('search:hit', parameters);
            this.searchResultCollection.search(
                this.sidePanel, parameters
            );
            this.searchResultCollection.fetch({
                success: function () {
                    self.searchResultCollection.renderCollection()
                }
            });
        },
        searchClick: function () {
            var searchValue = $('#search').val();
            if(searchValue.length < 3) {
                this.sidePanel.fillSidePanelHtml("<div id='search-results-container'>Minimal 3 characters</div>");
                return false
            }
            Shared.Router.clearSearch();
            this.search(searchValue);
        },
        searchEnter: function (e) {
            if (e.which === 13) {
                var searchValue = $('#search').val();
                if(searchValue.length < 3) {
                    this.sidePanel.fillSidePanelHtml("<div id='search-results-container'>Minimal 3 characters</div>");
                    return false
                }
                Shared.Router.clearSearch();
                this.search(searchValue);
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
            Shared.Dispatcher.on('search:searchCollection', this.search, this);
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