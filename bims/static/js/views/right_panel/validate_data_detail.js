define(['backbone', 'ol', 'shared', 'underscore', 'jquery'], function (Backbone, ol, Shared, _, $) {
    return Backbone.View.extend({
        template: _.template($('#validate-data-detail-container').html()),
        model: null,
        detailShowed: false,
        events: {
            'click .show-map-button': 'showOnMap',
            'click .show-detail': 'showDetail',
            'click .hide-detail': 'hideDetail',
            'click .accept-data': 'acceptData',
            'click .accept-validate': 'acceptValidate',
            'click .cancel-validate': 'cancelValidate',
            'click .reject-data': 'rejectData',
            'click .edit-data': 'editData',
            'click .accept-reject': 'acceptReject',
            'click .cancel-reject': 'cancelReject'
        },
        initialize: function () {
        },
        acceptValidate: function () {
            var self = this;
            var badges = $('<span class="badge badge-success">Accepted</span>');
            $.ajax({
                url: '/api/validate-object/',
                data: {'pk': self.model.get('id')},
                success: function () {
                    badges.insertAfter(self.$el.find('.accept-data'));
                    self.$el.find('.accept-data').css('display', 'none');
                    self.$el.find('.reject-data').css("display", "none");
                    self.$el.find('.validate-data-action').css("display", "none");
                }
            });
        },
        cancelValidate: function () {
            this.$el.find('.validate-data-action').css("display", "none");
            this.$el.find('.accept-data').css("display", "inline-block");
            this.$el.find('.reject-data').css("display", "inline-block");
        },
        acceptReject: function () {
            var self = this;
            var badges = $('<span class="badge badge-danger">Rejected</span>');
            $.ajax({
                url: '/api/reject-collection-data/',
                data: {
                    'pk': self.model.get('id'),
                    'rejection_message': self.$el.find('.rejection-message').val()
                },
                success: function () {
                    badges.insertAfter(self.$el.find('.reject-data'));
                    self.$el.find('.accept-data').css('display', 'none');
                    self.$el.find('.reject-data').css("display", "none");
                    self.$el.find('.reject-data-action').css("display", "none");
                }
            });
        },
        cancelReject: function () {
            this.$el.find('.reject-data-action').css("display", "none");
            this.$el.find('.accept-data').css("display", "inline-block");
            this.$el.find('.reject-data').css("display", "inline-block");
        },
        acceptData: function () {
            // Show validation
            this.$el.find('.validate-data-action').css("display", "block");
            this.$el.find('.accept-data').css("display", "none");
            this.$el.find('.reject-data').css("display", "none");
        },
        rejectData: function () {
            this.$el.find('.reject-data-action').css("display", "block");
            this.$el.find('.reject-data').css("display", "none");
            this.$el.find('.accept-data').css("display", "none");
        },
        editData: function () {
            window.open("/update/" + this.model.get('id'),"_self");
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
            this.$el.find('.validate-data-action').css("display", "none");
            this.$el.find('.reject-data-action').css("display", "none");
            return this;
        }
    })
});
