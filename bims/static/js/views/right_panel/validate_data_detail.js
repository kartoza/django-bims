define(['backbone', 'ol', 'shared', 'underscore', 'jquery'], function (Backbone, ol, Shared, _, $) {
    return Backbone.View.extend({
        template: _.template($('#validate-data-detail-container').html()),
        model: null,
        events: {
            'click .show-map-button': 'showOnMap'
        },
        initialize: function () {
        },
        showOnMap: function () {
            var location = JSON.parse(this.model.get('location'));
            var longitude = location.coordinates[0];
            var latitude = location.coordinates[1];
            var coordinates = [longitude, latitude];
            coordinates = ol.proj.transform(
                coordinates, ol.proj.get("EPSG:4326"), ol.proj.get("EPSG:3857"));

            Shared.Dispatcher.trigger('map:clearPoint');
            Shared.Dispatcher.trigger('map:drawPoint', coordinates, 10);
        },
        render: function () {
            var name = this.model.get('original_species_name');
            var description = this.model.get('category');
            var data = {
                id: this.model.get('id'),
                name: name,
                description: description
            };
            this.$el.html(this.template(data));
            return this;
        }
    })
});
