define(['backbone', 'views/olmap', 'shared'], function (Backbone, olmap, Shared) {

    return Backbone.Router.extend({
        parameters: {},
        routes: {
            "search/:query": "search"
        },
        initialize: function () {
            this.map = new olmap();
            $.ajax({
                type: 'GET',
                url: listCollectorAPIUrl,
                dataType: 'json',
                success: function (data) {
                    for (var i = 0; i < data.length; i++) {
                        $('#filter-collectors').append('<input type="checkbox" name="collector-value" value="' + data[i] + '"> ' + data[i] + '<br>');
                    }
                }
            });
            $.ajax({
                type: 'GET',
                url: listCategoryAPIUrl,
                dataType: 'json',
                success: function (data) {
                    for (var i = 0; i < data.length; i++) {
                        $('#filter-category').append('<input type="checkbox" name="category-value" value="' + data[i] + '">&nbsp;' + data[i] + '<br>');
                    }
                }
            });
        },
        search: function (query) {
            Shared.Dispatcher.trigger('search:searchCollection', query);
        },
        clearSearch: function () {
            this.navigate('', true);
        }
    })

});