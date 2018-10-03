define(['backbone', 'ol', 'shared', 'underscore', 'jquery'], function (Backbone, ol, Shared, _, $) {
    return Backbone.View.extend({
        template: _.template($('#validate-data-detail-container').html()),
        model: null,
        detailShowed: false,
        events: {
            'click .show-map-button': 'showOnMap',
            'click .show-detail': 'showDetail',
            'click .hide-detail': 'hideDetail'
        },
        initialize: function () {
        },
        showDetail: function () {
            this.$el.find('.detail-container').css("display", "block");
            this.$el.find('.hide-detail').css("display", "inline-block");
            this.$el.find('.show-detail').css("display", "none");
            this.detailShowed = true;
        },
        hideDetail: function () {
            this.$el.find('.detail-container').css("display", "none");
            this.$el.find('.show-detail').css("display", "inline-block");
            this.$el.find('.hide-detail').css("display", "none");
            this.detailShowed = false;
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
            this.$el.html(this.template(this.model.attributes));
            if (this.detailShowed) {
                this.showDetail();
            }
            return this;
        }
    })
});
