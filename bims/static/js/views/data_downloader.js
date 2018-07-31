define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        className: 'download-control-panel',
        template: _.template($('#download-control-panel').html()),
        url: '/api/collection/download/',
        events: {
            'click .download-control': 'toggleFormat',
            'click li': 'download'
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
            return this;
        },
        download: function (e) {
            this.parameters['fileType'] = $(e.target).data("format");
            var parameter = $.param(this.parameters);
            location.replace(this.url + '?' + parameter)
        },
        toggleFormat: function () {
            if ($('.download-format-selector-container').is(":hidden")) {
                this.parent.resetAllControlState();
                this.$el.find('.sub-control-panel').addClass('control-panel-selected');
                $('.download-format-selector-container').show();
            } else {
                this.$el.find('.sub-control-panel').removeClass('control-panel-selected');
                $('.download-format-selector-container').hide();
            }
        }
    })
});
