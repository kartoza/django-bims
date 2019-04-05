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
        initializeParameters: function () {
            this.parameters['taxon'] = '';
            this.parameters['months'] = '';
            this.parameters['siteId'] = '';
            this.parameters['search'] = '';
            this.parameters['collector'] = '';
            this.parameters['category'] = '';
            this.parameters['yearFrom'] = '';
            this.parameters['yearTo'] = '';
            this.parameters['userBoundary'] = '';
            this.parameters['referenceCategory'] = '';
            this.parameters['boundary'] = '';
            this.parameters['reference'] = '';
            this.parameters['endemic'] = '';
            this.parameters['conservationStatus'] = '';
            this.parameters['spatialFilter'] = '';
            this.parameters['taxon'] = '';
            this.parameters['validated'] = '';
            this.parameters['modules'] = '';
            if (typeof filterParameters !== 'undefined') {
                filterParameters = $.extend(true, {}, this.parameters);
            }
        },
        initialize: function () {
            this.initializeParameters();
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