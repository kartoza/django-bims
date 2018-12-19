define(['backbone', 'views/olmap', 'utils/events_connector', 'shared'], function (Backbone, olmap, EventsConnector, Shared) {

    return Backbone.Router.extend({
        parameters: {},
        searchHistory: [],
        routes: {
            "": "toMap",
            "search/:query": "search",
            "search/:query/:filters": "searchWithFilters",
            "search//:filters": "onlyFilters",
            "site-detail/:query": "showSiteDetailedDashboard",
            "species-detail/:query": "showSpeciesDetailedDashboard"
        },
        initialize: function () {
            this.map = new olmap();
            this.eventsConnector = new EventsConnector();
        },
        search: function (query) {
            var searchControl = $('.search-control');
            if (!searchControl.hasClass('control-panel-selected')) {
                searchControl.click();
            }
            $('#search').val(query);
            Shared.Dispatcher.trigger('search:checkSearchCollection', true);
            this.searchHistory.push(query);
        },
        searchWithFilters: function (query, filters) {
            // Get all filters
            var windowHash = window.location.hash;
            var firstFilterWord = filters.slice(0, 5);
            var newFilter = windowHash.slice(windowHash.indexOf(firstFilterWord));
            Shared.Dispatcher.trigger('filters:updateFilters', newFilter);
            if (this.searchHistory.length < 1) {
                this.search(query);
            }
        },
        onlyFilters: function (filters) {
            // Get all filters
            var windowHash = window.location.hash;
            var firstFilterWord = filters.slice(0, 5);
            var newFilter = windowHash.slice(windowHash.indexOf(firstFilterWord));
            Shared.Dispatcher.trigger('filters:updateFilters', newFilter);
            this.search('');
        },
        showSiteDetailedDashboard: function (query) {
            Shared.Dispatcher.trigger('map:showSiteDetailedDashboard', query);
        },
        showSpeciesDetailedDashboard: function (query) {
            Shared.Dispatcher.trigger('map:showTaxonDetailedDashboard', query);
        },
        clearSearch: function () {
            this.navigate('', false);
        },
        toMap: function () {
            Shared.Dispatcher.trigger('map:closeDetailedDashboard');
        },
        updateUrl: function (url, trigger) {
            if (!trigger) {
                this.navigate(url, {trigger: false});
            } else {
                this.navigate(url, {trigger: true});
            }
        }
    })
});