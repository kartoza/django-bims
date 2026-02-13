define(['backbone', 'views/olmap', 'utils/events_connector', 'shared'], function (Backbone, olmap, EventsConnector, Shared) {

    return Backbone.Router.extend({
        parameters: {},
        searchHistory: [],
        routes: {
            "": "toMap",
            "search/:query": "search",
            "search/:query/:filters": "searchWithFilters",
            "search//(:filter)(/):filters": "onlyFilters",
            "site-detail/:query": "showSiteDetailedDashboard",
            "species-detail/:query": "showSpeciesDetailedDashboard",
            "site/:params": "showSingleSiteDetail"
        },
        initializeParameters: function () {
            const parameterKeys = [
                'taxon', 'months', 'siteId', 'search', 'collector',
                'category', 'yearFrom', 'yearTo', 'userBoundary', 'referenceCategory',
                'boundary', 'reference', 'endemic', 'invasions', 'conservationStatus', 'spatialFilter',
                'taxon', 'validated', 'modules', 'sourceCollection', 'datasetKeys', 'ecologicalCategory',
                'module', 'tags', 'rank', 'orderBy', 'siteIdOpen', 'polygon',
                'dst', 'ecosystemType', 'asf'
            ];

            parameterKeys.forEach(key => {
                this.parameters[key] = '';
            });

            if (typeof filterParameters !== 'undefined') {
                filterParameters = $.extend(true, {}, this.parameters);
            }
        },
        initialize: function () {
            let self = this;
            this.defaultFiltersExist = false;
            this.defaultFiltersParam = '';
            this.initializeParameters();
            this.defaultSelectedFilters = JSON.parse(mapDefaultSelectedFilters.replace(/u'/g, '\'').replace(/'/g, '"'));
            this.map = new olmap();
            this.eventsConnector = new EventsConnector();

        },
        search: function (query) {
            var searchControl = $('.search-control');
            if (!searchControl.hasClass('control-panel-selected')) {
                searchControl.click();
            }
            $('#search').val(query);
            if (this.searchHistory.length === 0) {
                Shared.Dispatcher.trigger('search:checkSearchCollection', true);
            }
            this.searchHistory.push(query);
        },
        searchWithFilters: function (query, filters) {
            // Get all filters
            var windowHash = window.location.hash;
            var firstFilterWord = filters.slice(0, 5);
            var newFilter = windowHash.slice(windowHash.indexOf(firstFilterWord));
            if (this.searchHistory.length < 1) {
                Shared.Dispatcher.trigger('filters:updateFilters', newFilter, true);
                this.search(query);
            } else {
                Shared.Dispatcher.trigger('filters:updateFilters', newFilter, false);
            }
        },
        onlyFilters: function (filters) {
            // Get all filters
            var windowHash = window.location.hash;
            var firstFilterWord = filters.slice(0, 5);
            var newFilter = windowHash.slice(windowHash.indexOf(firstFilterWord));
            if (this.searchHistory.length < 1) {
                Shared.Dispatcher.trigger('filters:updateFilters', newFilter, true);
                this.search('');
            } else {
                Shared.Dispatcher.trigger('filters:updateFilters', newFilter, false);
            }
        },
        showSiteDetailedDashboard: function (query) {
            Shared.Dispatcher.trigger('map:showSiteDetailedDashboard', query);
        },
        showSpeciesDetailedDashboard: function (query) {
            Shared.Dispatcher.trigger('map:showTaxonDetailedDashboard', query);
        },
        clearSearch: function () {
            this.navigate('', false);
            this.toMap();
        },
        showSingleSiteDetail: function (params) {
            let siteId = '';
            if (params) {
                siteId = params.split('siteIdOpen=')[1];
            }
            if (siteId) {
                siteId = siteId.split('&')[0];
                Shared.Dispatcher.trigger('siteDetail:show', siteId, '', true);
            }
        },
        toMap: function () {
            let self = this;
            if (!this.defaultFiltersParam) {
                $.each(this.defaultSelectedFilters, function (index, selectedFilter) {
                    if (self.parameters.hasOwnProperty(selectedFilter['filter_key'])) {
                        self.parameters[selectedFilter['filter_key']] = JSON.stringify(selectedFilter['filter_values']);
                        self.defaultFiltersExist = true;
                    }
                });
            }
            if (this.defaultFiltersExist && !this.defaultFiltersParam) {
                this.defaultFiltersParam = $.param(self.parameters);
            }
            if (this.defaultFiltersParam) {
                Shared.Dispatcher.trigger('filters:updateFilters', this.defaultFiltersParam, false);
            }

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