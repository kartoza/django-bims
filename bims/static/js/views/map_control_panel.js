define(['backbone', 'underscore', 'jquery', 'ol', 'views/search'], function (Backbone, _, $, ol, SearchView) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        locationControlActive: false,
        searchView: null,
        events: {
            'click .search-control': 'searchClicked',
            'click .filter-control': 'filterClicked',
            'click .location-control': 'locationClicked',
            'click .map-search-close': 'closeSearchPanel',
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
        },
        searchClicked: function (e) {
            // show search div
            if(!this.searchView.isOpen()) {
                this.openSearchPanel();
            } else {
                this.closeSearchPanel();
            }
        },
        filterClicked: function (e) {
        },
        locationClicked: function (e) {
            var target = $(e.target);
            if(!target.hasClass('location-control')) {
                target = target.parent();
            }
            // Activate function
            if(!this.locationControlActive) {
                this.locationControlActive = true;
                target.addClass('control-panel-selected');
            } else {
                this.locationControlActive = false;
                target.removeClass('control-panel-selected');
                this.parent.hideGeoContext();
            }
        },
        render: function () {
            this.$el.html(this.template());

            this.searchView = new SearchView({
                parent: this,
                sidePanel: this.parent.sidePanelView
            });

            this.$el.append(this.searchView.render().$el);

            return this;
        },
        openSearchPanel: function () {
            this.$el.find('.search-control').addClass('control-panel-selected');
            this.searchView.show();
        },
        closeSearchPanel: function () {
            this.$el.find('.search-control').removeClass('control-panel-selected');
            this.searchView.hide();
        },
        closeAllPanel: function () {
            this.closeSearchPanel();
        }
    })
});
