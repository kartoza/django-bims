define(['backbone', 'models/search_result', 'shared', 'underscore', 'ol'], function (Backbone, SearchResult, Shared, _, ol) {
    return Backbone.View.extend({
        id: 0,
        data: null,
        events: {
            'click': 'clicked'
        },
        initialize: function (options) {
            this.render();
        },
        clicked: function (e) {
            if (this.getResultType() == 'bio') {
                Shared.Dispatcher.trigger(
                    'searchResult:clicked',
                    this.model.get('taxon_gbif_id'),
                    this.model.get('common_name')
                );
            } else if (this.getResultType() == 'taxa') {
                Shared.Dispatcher.trigger('searchResult:clicked',
                    this.model.get('id'),
                    this.model.get('common_name')
                );
            }
        },
        getResultType: function () {
            return this.model.attributes.record_type;
        },
        render: function () {
            this.data = this.model.toJSON();
            if (this.getResultType() == 'bio') {
                var template = _.template($('#search-result-record-template').html());
                this.$el.html(
                    template(this.model.attributes)
                );
                $('#biological-record-list').append(this.$el);
            } else if (this.getResultType() == 'taxa') {
                var template = _.template($('#search-result-taxa-template').html());
                this.$el.html(template(this.model.attributes));
                $('#taxa-list').append(this.$el);
            } else if (this.getResultType() == 'site') {
                var template = _.template($('#search-result-site-template').html());
                this.$el.html(template(this.model.attributes));
                $('#site-list').append(this.$el);
            }
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
