define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        template: _.template($('#map-search-result-template').html()),
        events: {
            'click .map-result-close': 'closeSidePanelAnimation'
        },
        initialize: function () {
        },
        render: function () {
            this.$el.html(this.template());
            this.$el.hide()
            return this;
        },
        updatesearchPanelTitle: function (title) {
            this.$el.find('.search-box').html(title);
        },
        fillPanelHtml: function (htmlData) {
            this.$el.find('#search-result-content').html(htmlData);
        },
        showSearchLoading: function () {
            this.$el.find('#search-result-content').html('' +
                '<img src="/static/img/small-loading.svg" alt="Loading view">');
        },
        show: function () {
            this.$el.show()
        },
        hide: function () {
            this.$el.hide()
        },
        openSidePanel: function () {
            this.$el.show();
        },
        clearSidePanel: function () {
            this.$el.find('.search-box').html('');
            this.$el.find('#search-result-content').html('');
        },
        closeSidePanelAnimation: function () {
            this.$el.hide();
            this.clearSidePanel();
        },
        isPanelOpen: function () {
            return this.$el.is(":visible");
        }
    })
});
