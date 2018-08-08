define(['backbone', 'views/olmap', 'shared'], function (Backbone, olmap, Shared) {

    return Backbone.Router.extend({
        parameters: {},
        routes: {
            "search/:query": "search"
        },
        initialize: function () {
            this.map = new olmap();
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