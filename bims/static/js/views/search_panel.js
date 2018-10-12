define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'views/political_region', 'jquery'], function (Shared, Backbone, _, jqueryUi, PoliticalRegion, $) {
    return Backbone.View.extend({
        template: _.template($('#map-search-result-template').html()),
        events: {
            'click .map-result-close': 'closeSidePanelAnimation'
        },
        initialize: function () {
            this.politicalRegion = new PoliticalRegion();
        },
        render: function () {
            this.$el.html(this.template());
            this.$el.hide();
            this.politicalRegion.render(this.$el);
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
            $('.map-search-result').show();
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
