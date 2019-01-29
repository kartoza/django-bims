define(['backbone', 'models/search_result', 'shared', 'underscore', 'jquery'], function (Backbone, SearchResult, Shared, _, $) {
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
            if (this.getResultType() === 'taxa') {
                Shared.Dispatcher.trigger('searchResult:taxonClicked', this.model.attributes);
            } else if (this.getResultType() === 'site') {
                Shared.Dispatcher.trigger('searchResult:siteClicked', this.model.attributes);
            } else if (this.getResultType() === 'show-more-site') {
                console.log('Show more site');
            }
        },
        getResultType: function () {
            return this.model.attributes.record_type;
        },
        render: function () {
            this.data = this.model.toJSON();
            if (this.getResultType() === 'taxa') {
                var template = _.template($('#search-result-taxa-template').html());
                this.$el.html(template(this.model.attributes));
                $('#taxa-list').append(this.$el);
            } else if (this.getResultType() === 'site') {
                var template = _.template($('#search-result-site-template').html());
                this.$el.html(template(this.model.attributes));
                $('#site-list').append(this.$el);
            } else if (this.getResultType() === 'show-more-site') {
                var template = _.template($('#show-more-result-site-template').html());
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
