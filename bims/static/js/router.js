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
            Shared.Dispatcher.trigger('search:searchCollection', query);
        },
        clearSearch: function () {
            this.navigate('', true);
        }
    })

});