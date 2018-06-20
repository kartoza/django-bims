define(['backbone', 'models/search_result', 'shared', 'underscore', 'ol'], function (Backbone, SearchResult, Shared, _, ol) {
    return Backbone.View.extend({
        id: 0,
        data: null,
        sidePanel: null,
        template: _.template($('#search-result-template').html()),
        events: {
            'click': 'clicked'
        },
        initialize: function (options) {
            this.sidePanel = options.sidePanel;
            this.render();
        },
        clicked: function (e) {
            var geometry = JSON.parse(this.model.attributes['geometry']);
            var coordinates = ol.proj.transform(geometry['coordinates'], "EPSG:4326", "EPSG:3857");
            var zoomLevel = 15;
            Shared.Dispatcher.trigger('map:zoomToCoordinates', coordinates, zoomLevel);
        },
        render: function () {
            this.data = this.model.toJSON();
            this.$el.html(this.template(this.model.attributes));
            this.sidePanel.appendSidePanelContent(this.$el);
        },
        destroy: function () {
            this.unbind();
            this.model.destroy();
            return Backbone.View.prototype.remove.call(this);
        }
    })
});
