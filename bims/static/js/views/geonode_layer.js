define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        className: 'geonode-layer-control-panel',
        template: _.template($('#geonode-layer-control-panel').html()),
        events: {
            'click .geonode-layer-control': 'toggleFormat',
            'click .map-search-close': 'closeGeonodeLayerPanel',
        },
        initialize: function (options) {
            this.parent = options.parent;
        },
        render: function () {
            this.$el.html(this.template());
            return this;
        },
        toggleFormat: function () {
            if ($('.geonode-layer-search-box').is(":hidden")) {
                this.parent.resetAllControlState();
                this.$el.find('.sub-control-panel').addClass('control-panel-selected');
                $('.geonode-layer-search-box').show();
            } else {
                this.$el.find('.sub-control-panel').removeClass('control-panel-selected');
                $('.geonode-layer-search-box').hide();
            }
        },
        closeGeonodeLayerPanel: function () {
             if (!$('.geonode-layer-search-box').is(":hidden")) {
                this.$el.find('.sub-control-panel').removeClass('control-panel-selected');
                $('.geonode-layer-search-box').hide();
            }
        }
    })
});
