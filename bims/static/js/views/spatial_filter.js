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
            });

            self.fileupload.bind('fileuploadstop', function (e) {
                self.progress.html('Processing...');
                self.progress.show();
                $.ajax({
                    url: '/process_user_boundary_shapefiles/',
                    data: {
                        token: csrfmiddlewaretoken
                    },
                    dataType: 'json',
                    success: function (data) {
                        self.progress.html(data.message);
                    }
                })
            });

            return this;
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
