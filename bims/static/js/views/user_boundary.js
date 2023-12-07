define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery', 'ol'], function (Shared, Backbone, _, jqueryUi, $, ol) {
    return Backbone.View.extend({
        template: _.template($('#user-boundary-template').html()),
        geojson: '',
        saveModalName: 'user-boundary-save-modal',
        events: {
            'click #save-polygon-btn': 'savePolygon',
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
        },
        render: function () {
            this.$el.html(this.template());
            return this;
        },
        savePolygon: function () {
            let $modal = $('#' + this.saveModalName);
            let boundaryNameInput = $('#user-boundary-name');
            if (!boundaryNameInput.val()) {
                boundaryNameInput.focus();
                return;
            }
            $modal.find('button').prop('disabled', true);
            boundaryNameInput.prop('disabled', true);
            $modal.find('.alert').hide();

            $.ajax({
                type: 'POST',
                url: '/process_user_boundary_geojson/',
                data: {
                    'geojson': this.geojson,
                    'name': boundaryNameInput.val()
                },
            }).done(function (result) {
                $modal.find('.alert-success').show();
                $modal.find('.alert-success').html(result.message);
            }).fail(function () {
                $modal.find('.alert-danger').show();
            }).always(function () {
                $modal.find('button').prop('disabled', false);
                boundaryNameInput.prop('disabled', false);
            });
        },
        showSaveModal: function (geojsonStr) {
            let $modalSelector = $('#' + this.saveModalName);
            this.geojson = geojsonStr;
            $modalSelector.modal({
                backdrop: 'static',
                keyboard: false
            });
            $modalSelector.on('shown.bs.modal', function () {
                $('#user-boundary-name').focus();
            });
            $modalSelector.modal('show');
        },
    })
});
