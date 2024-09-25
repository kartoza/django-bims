define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery'], function (Shared, Backbone, _, jqueryUi, $) {
    return Backbone.View.extend({
        template: _.template($('#user-boundary-template').html()),
        geojson: '',
        saveModalName: 'user-boundary-save-modal',
        loadModalName: 'user-boundary-load-modal',
        selectedSavedPolygon: null,
        events: {
            'click #save-polygon-btn': 'savePolygon',
            'click #load-polygon-btn': 'loadPolygon',
            'click #delete-polygon-btn': 'deletePolygon'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
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
                headers: {"X-CSRFToken": csrfmiddlewaretoken},
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
        showLoadModal: function () {
            let self = this;
            let $modal = $('#' + this.loadModalName);
            $modal.modal({
                backdrop: 'static',
                keyboard: false
            });
            let $modalBody = $modal.find('.modal-body');
            $modal.find('.btn-action').prop('disabled', true);

            $modalBody.html(`
                <div style="width: 100%; text-align: center">
                    <img src="/static/img/small-loading.svg" width="25" alt="Loading view">
                </div>
            `);
            $modal.modal('show');

            $.ajax({
                type: 'GET',
                url: '/api/user-boundaries/',
                headers: {"X-CSRFToken": csrfmiddlewaretoken},
            }).done(function (result) {
                $modalBody.empty();
                if (result && Array.isArray(result) && result.length > 0) {
                    const $listGroup = $('<div class="list-group"></div>');
                    result.forEach(function (boundary) {
                        const formattedDate = new Date(boundary['upload_date']).toLocaleString();
                        const $item = $(`
                            <a href="#" class="list-group-item list-group-item-action" id="user-boundary-item-${boundary.id}">
                                ${boundary.name}
                                <small class="d-block">${formattedDate}</small>
                            </a>
                        `);
                        $listGroup.append($item);
                        $item.on('click', function (evt) {
                            $modal.find('.active').removeClass('active');
                            $modal.find('.btn-action').prop('disabled', false);
                            $(evt.currentTarget).addClass('active');
                            self.selectedSavedPolygon = boundary.id;
                        })
                    });
                    $modalBody.append($listGroup);
                } else {
                    $modalBody.append('<p>No boundaries found.</p>');
                }
            });
        },
        loadPolygon: function (fitToExtent = true) {
            let $modal = $('#' + this.loadModalName);
            $modal.find('button').prop('disabled', true);
            let self = this;

            $.ajax({
                type: 'GET',
                url: `/api/user-boundary/${this.selectedSavedPolygon}/`,
                headers: {"X-CSRFToken": csrfmiddlewaretoken},
            }).done(function (result) {
                $modal.find('button').prop('disabled', false);
                $modal.modal('hide');
                self.parent.drawGeojson(result, fitToExtent);
            });
        },
        deletePolygon: function () {
            if (confirm('Are you sure you want to permanently delete this boundary?') === false) {
                return false;
            }
            let self = this;
            let $modal = $('#' + this.loadModalName);
            $modal.find('.btn-action').prop('disabled', true);
            $.ajax({
                url: '/api/delete-user-boundary/' + self.selectedSavedPolygon,
                type: 'DELETE',
                headers: {"X-CSRFToken": csrfmiddlewaretoken},
            })
            .done(function(result) {
                $('#user-boundary-item-' + self.selectedSavedPolygon).remove();
                self.selectedSavedPolygon = null;
                $modal.find('.btn-action').prop('disabled', true);
            })
            .fail(function(xhr, status, error) {
                $modal.find('.btn-action').prop('disabled', false);
                console.log('Error in Deletion: ', xhr.responseText);
            });
        }
    })
});
