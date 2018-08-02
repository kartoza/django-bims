define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        className: 'geonode-layer-control-panel',
        template: _.template($('#geonode-layer-control-panel').html()),
        events: {
            // 'click .download-control': 'toggleFormat',
            // 'click li': 'download'
        },
        initialize: function (options) {
            this.parent = options.parent;
        },
        render: function () {
            this.$el.html(this.template());
            return this;
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
