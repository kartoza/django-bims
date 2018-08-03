define(['shared', 'backbone', 'views/data_downloader-modal', 'underscore', 'jqueryUi'], function (Shared, Backbone, Modal, _) {
    return Backbone.View.extend({
        className: 'download-control-panel',
        template: _.template($('#download-control-panel').html()),
        events: {
            'click .download-control': 'toggleFormat'
        },
        initialize: function (options) {
            this.parent = options.parent;
            this.modal = new Modal({
                parent: this
            });
        },
        render: function () {
            this.$el.html(this.template());
            return this;
        },
        renderModal: function () {
            return this.modal.render().$el;
        },
        toggleFormat: function () {
            if (!this.$el.find('.sub-control-panel').hasClass('control-panel-selected')) {
                this.parent.resetAllControlState();
                this.$el.find('.sub-control-panel').addClass('control-panel-selected');
                this.modal.showModal();
            } else {
                this.$el.find('.sub-control-panel').removeClass('control-panel-selected');
                $('#download-control-modal').hide();
            }
        }
    })
});
