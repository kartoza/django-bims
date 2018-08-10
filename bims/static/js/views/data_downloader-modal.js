define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        template: _.template($('#download-control-panel-template').html()),
        url: '/api/collection/download/',
        events: {
            'click .close': 'closeModal',
            'click #go-button': 'searchCoordinate',
            'click .row-format': 'download'
        },
        parameters: {
            taxon: '', zoom: 0, bbox: [],
            collector: '', category: '', yearFrom: '', yearTo: '', months: ''
        },
        initialize: function (options) {
            Shared.Dispatcher.on('cluster:updated', this.updateParameters, this);
            this.parent = options.parent;
        },
        updateParameters: function (parameters) {
            var self = this;
            $.each(parameters, function (key, value) {
                self.parameters[key] = value;
            });
        },
        render: function () {
            this.$el.html(this.template());
            this.modal = this.$el.find('.modal');
            this.notification = this.$el.find('.notification');
            return this;
        },
        showModal: function () {
            this.modal.show();
        },
        closeModal: function () {
            this.modal.hide();
            this.parent.toggleFormat();
        },
        resetModal: function () {
            $(this.notification).html('');
            $(this.notification).hide();
            this.$el.find('.row-format').removeClass('disabled');
        },
        download: function (e) {
            if ($(e.target).hasClass('disabled')) {
                return;
            }
            var format = $(e.target).data("format");
            this.parameters['fileType'] = format;

            if (format == 'csv') {
                $(this.notification).html('downloading ' + format);
                $(this.notification).show();
                this.$el.find('.row-format').addClass('disabled');

                var parameter = $.param(this.parameters);
                var url = this.url + '?' + parameter;
                if (this.xhr) {
                    this.xhr.abort();
                }
                this.downloading(url);
            } else {
                location.replace(this.url + '?' + parameter)
            }

        },
        downloading: function (url) {
            var self = this;
            self.xhr = $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    if (data['status'] !== "success") {
                        setTimeout(
                            function () {
                                self.downloading(url);
                            }, 5000);
                    } else {
                        self.downloadFile(data);
                    }
                },
                error: function (req, err) {
                }
            });
        },
        downloadFile: function (data) {
            var is_safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
            if(is_safari) {
                var a = window.document.createElement('a');
                a.href = '/uploaded/csv_processed/' + data['filename'];
                a.download = data['filename'];
                a.click();
            } else {
                location.replace('/uploaded/csv_processed/' + data['filename']);
            }

            this.resetModal();
        }
    })
});
