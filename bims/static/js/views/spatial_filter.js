define([
    'backbone',
    'underscore',
    'jquery',
    'shared',
    'ol',
    'jquery.fileupload',
    'jquery.fileupload-process',
    'jquery.fileupload-validate'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        template: _.template($('#spatial-filter-panel').html()),
        events: {
            'click .close-button': 'close',
            'click #spatial-filter-panel-upload': 'panelUploadClicked',
            'click .close-upload-boundary-modal': 'closeModal',
            'click .btn-boundary-upload': 'btnUploadClicked'
        },
        render: function () {
            var self = this;

            self.$el.html(this.template());
            self.$el.find('.map-control-panel-box').hide();
            self.fileupload = self.$el.find('#fileupload');
            self.uploadButton = self.$el.find('.btn-boundary-upload');
            self.progress = self.$el.find('.process-shapefile');
            self.boundaryListContainer = self.$el.find('.boundary-list');
            self.boundaryInputText = self.$el.find('input#boundary-input-name.form-control');

            self.getUserBoundary();

            self.progress.hide();

            self.fileupload.fileupload({
                acceptFileTypes: /(\.|\/)(shp|shx|dbf)$/i,
                dataType: 'json',
                done: function (e, data) {
                    if (data.result.is_valid) {
                        self.$el.find("#file-list tbody").prepend(
                            "<tr><td><a href='" + data.result.url + "'>" +
                            data.result.name + "</a></td></tr>"
                        )
                    }
                }
            });

            self.fileupload.bind('fileuploadprogress', function (e, data) {
                self.uploadButton.hide();
                self.progress.html('Uploading...');
                self.progress.show();
                self.$el.find('#file-list tbody').html('');
            });

            self.fileupload.bind('fileuploadstop', function (e) {
                self.uploadButton.show();
                self.progress.html('Processing...');
                self.progress.show();
                var userBoundaryName = self.boundaryInputText.val();
                $.ajax({
                    url: '/process_user_boundary_shapefiles/',
                    data: {
                        token: csrfmiddlewaretoken,
                        name: userBoundaryName
                    },
                    dataType: 'json',
                    success: function (data) {
                        self.boundaryInputText.val('');
                        self.uploadButton.prop('disabled', true);
                        self.progress.html(data.message);
                        if (data.message === 'User boundary added') {
                            self.getUserBoundary();
                        }
                    }
                })
            });

            self.boundaryInputText.on('input', function (e) {
                var input = $(this);
                var val = input.val();

                if(val.length >= 3) {
                    self.uploadButton.prop('disabled', false);
                } else {
                    self.uploadButton.prop('disabled', true);
                }

            });

            return this;
        },
        getUserBoundary: function () {
            var self = this;
            if(!is_logged_in) {
                return false;
            }
            $.ajax({
                url: '/api/list-user-boundary/',
                dataType: 'json',
                success: function (data) {
                    Shared.Dispatcher.UserBoundaries = data;
                    self.boundaryListContainer.html('');
                    $.each(data['features'], function (index, feature) {
                        var name = feature['properties']['name'];
                        var id = feature['id'];
                        var div = $('<div data-id="'+id+'">'+feature['properties']['name']+'</div>');
                        self.boundaryListContainer.append(div);
                        div.on('click', self.boundaryListClicked);
                    })
                }
            })
        },
        boundaryListClicked: function (e) {
            var self = this;
            var id = $(e.target).data('id');
            var boundary = {};
            $.each(Shared.Dispatcher.UserBoundaries['features'], function (index, feature) {
                if (feature['id'] === id) {
                    boundary = feature;
                    return true;
                }
            });
            var feature = new ol.format.GeoJSON().readFeatures(
                boundary, {
                    featureProjection: 'EPSG:3857'
                }
            );

            Shared.Dispatcher.trigger('map:switchHighlightPinned', feature, true);
            Shared.Dispatcher.trigger('map:zoomToHighlightPinnedFeatures');
            Shared.Dispatcher.trigger('search:addUserBoundaryFilter', id);
        },
        isOpen: function () {
            return !this.$el.find('.map-control-panel-box').is(':hidden');
        },
        show: function () {
            this.$el.find('.map-control-panel-box').show();
        },
        close: function () {
            this.hide();
        },
        hide: function () {
            this.$el.find('.map-control-panel-box').hide();
        },
        panelUploadClicked: function (e) {
            // Show upload modal
            Shared.Dispatcher.trigger('mapControlPanel:clickSpatialFilter');
            this.boundaryInputText.val('');
            this.uploadButton.prop('disabled', true);
            this.$el.find('.modal').show();
        },
        closeModal: function (e) {
            this.$el.find('.modal').hide();
        },
        btnUploadClicked: function (e) {
            this.fileupload.click();
        },
        fileUpload: function () {

        }
    })
});
