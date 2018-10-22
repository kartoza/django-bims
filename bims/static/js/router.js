define(['backbone', 'views/olmap', 'utils/events_connector', 'shared'], function (Backbone, olmap, EventsConnector, Shared) {

    return Backbone.Router.extend({
        parameters: {},
        routes: {
            "search/:query": "search"
        },
        initialize: function () {
            this.map = new olmap();
            this.eventsConnector = new EventsConnector();
        },
        search: function (query) {
            if ($('.search-control').is(":visible")) {
                $('.search-control').click();
            }
            $('#search').val(query);
            Shared.Dispatcher.trigger('search:checkSearchCollection', true);
        },
        clearSearch: function () {
            this.navigate('', true);
        }
    })

});