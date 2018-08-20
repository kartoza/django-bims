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
            if (this.getResultType() === 'taxa') {
                Shared.Dispatcher.trigger('searchResult:updateTaxon',
                    this.model.get('id'),
                    this.model.get('species')
                );
                Shared.Dispatcher.trigger('taxonDetail:show',
                    this.model.get('id'),
                    this.model.get('species')
                );
            } else if (this.getResultType() === 'site') {
                Shared.Dispatcher.trigger('siteDetail:show',
                    this.model.get('id'), this.model.get('name'));
                if (this.model.get('geometry')) {
                    var feature = {
                        id: this.model.get('id'),
                        type: "Feature",
                        geometry: JSON.parse(this.model.get('geometry')),
                        properties: {}
                    };
                    var features = new ol.format.GeoJSON().readFeatures(feature, {
                        featureProjection: 'EPSG:3857'
                    });
                    Shared.Dispatcher.trigger('map:switchHighlight', features);
                }
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
            }
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
