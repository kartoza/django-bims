define(['backbone', 'models/search_result', 'shared', 'underscore', 'ol'], function (Backbone, SearchResult, Shared, _, ol) {
    return Backbone.View.extend({
        id: 0,
        data: null,
        template: _.template($('#search-result-template').html()),
        events: {
            'click': 'clicked'
        },
        initialize: function (options) {
            this.render();
        },
        clicked: function (e) {
            Shared.Dispatcher.trigger('searchResult:clicked', this.model.get('taxon_gbif_id'));
        },
        render: function () {
            this.data = this.model.toJSON();
            this.$el.html(this.template(this.model.attributes));
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
