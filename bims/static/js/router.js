define(['backbone', 'views/olmap', 'utils/events_connector', 'shared'], function (Backbone, olmap, EventsConnector, Shared) {

    return Backbone.Router.extend({
        parameters: {},
        routes: {
            "": "toMap",
            "search/:query": "search",
            "site-detail/:query": "showSiteDetailedDashboard"
        },
        initialize: function () {
            this.map = new olmap();
            this.eventsConnector = new EventsConnector();
        },
        search: function (query) {
            var searchControl = $('.search-control');
            if (searchControl.is(":visible")) {
                searchControl.click();
            }
            $('#search').val(query);
            Shared.Dispatcher.trigger('search:checkSearchCollection', true);
        },
        showSiteDetailedDashboard: function (query) {
            Shared.Dispatcher.trigger('map:showSiteDetailedDashboard', query);
        },
        clearSearch: function () {
            this.navigate('', true);
        },
        toMap: function () {
            Shared.Dispatcher.trigger('map:closeDetailedDashboard');
        }
    })
});