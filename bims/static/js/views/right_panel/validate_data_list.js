define([
    'backbone',
    'ol',
    'shared',
    'underscore',
    'views/right_panel/validate_data_detail',
    'collections/validate_data'], function (Backbone, ol, Shared, _, ValidateDataDetail, ValidateDataCollection) {
    return Backbone.View.extend({
        opened: false,
        currentPage: 1,
        collections: {},
        events: {
            'click .show-map-button': 'showMapButtonClicked'
        },
        template: _.template($('#validate-data-list-container').html()),
        initialize: function (options) {
            // Register events
            this.sidePanel = options.parent;
            Shared.Dispatcher.on('validateData:show', this.show, this);
            this.validateDataCollection = new ValidateDataCollection();
            this.validateDataCollection.updateUrl(this.currentPage);
        },
        render: function () {
            this.$el.html(this.template());
            return this;
        },
        show: function () {
            this.opened = true;
            this.updateTitle();
            this.fetchCollection();
        },
        close: function () {
            this.opened = false;
            this.triggerEvent('closeSidePanel');
        },
        isOpen: function () {
            return this.opened;
        },
        fetchCollection: function () {
            var self = this;
            if(!self.collections[self.currentPage]) {
                var collection = new ValidateDataCollection();
                collection.updateUrl(self.currentPage);
                collection.fetch({
                    success: function () {
                        self.renderList();
                    }
                });
                self.collections[self.currentPage] = collection;
            } else {
                self.renderList();
            }
        },
        updateTitle: function () {
            var title = 'Validate Data';
            this.sidePanel.updateSidePanelTitle(title);
        },
        renderList: function () {
            var self = this;
            $.each(self.collections[self.currentPage].models, function (index, model) {
                var detailView = new ValidateDataDetail();
                detailView.model = model;
                self.$el.find('.wrapper').append(detailView.render().$el);
            });
            // listTemplate.find('.show-map-button').click(this.showMapButtonClicked);
        },
        showMapButtonClicked: function (e) {
            var id = $(e.target).parent().data('id');
            console.log(id);
            // console.log(this.collections[this.currentPage]);
        },
        triggerEvent: function (eventName, parameters) {
            Shared.Dispatcher.trigger('sidePanel:'+eventName, parameters);
        }
    })
});
