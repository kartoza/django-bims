define(['backbone', 'underscore', 'jquery', 'shared', 'ol'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        template: _.template($('#upload-data-modal').html()),
        locateCoordinateModal: null,
        events: {
            'click .close': 'closeModal',
            'click #go-button': 'searchCoordinate',
        },
        render: function () {
            this.$el.html(this.template());
            this.locateCoordinateModal = this.$el.find('.modal');
            return this;
        },
        showModal: function () {
            this.locateCoordinateModal.show();
        },
        closeModal: function () {
            this.locateCoordinateModal.hide();
        },
        searchCoordinate: function (e) {
            var longitude = parseFloat($('#longitude').val());
            var latitude = parseFloat($('#latitude').val());
            var coordinates = [longitude, latitude];
            coordinates = ol.proj.transform(
                coordinates, ol.proj.get("EPSG:4326"), ol.proj.get("EPSG:3857"));
            Shared.Dispatcher.trigger('map:zoomToCoordinates', coordinates, 17);
            this.closeModal();
        },
    })
});