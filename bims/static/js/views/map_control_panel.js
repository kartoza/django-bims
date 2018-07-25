define([
    'backbone', 'underscore', 'jquery', 'ol', 'views/search', 'views/locate', 'views/data_downloader'
], function (Backbone, _, $, ol, SearchView, LocateView, DataDownloader) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        locationControlActive: false,
        searchView: null,
        locateView: null,
        events: {
            'click .search-control': 'searchClicked',
            'click .filter-control': 'filterClicked',
            'click .locate-control': 'locateClicked',
            'click .location-control': 'locationClicked',
            'click .map-search-close': 'closeSearchPanel',
            'click .layers-selector-container-close': 'closeFilterPanel',
            'click .locate-options-container-close': 'closeLocatePanel',
            'click .sub-filter': 'closeSubFilter',
            'click .locate-coordinates': 'openLocateCoordinates',
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.dataDownloaderControl = new DataDownloader({
                parent: this
            });
        },
        resetAllControlState: function () {
            $('.layer-switcher.shown button').click();
            $('.map-control-panel-box:visible').hide();
            $('.sub-control-panel.control-panel-selected').removeClass('control-panel-selected');
        },
        searchClicked: function (e) {
            // show search div
            if (!this.searchView.isOpen()) {
                this.resetAllControlState();
                this.openSearchPanel();
                this.closeFilterPanel();
                this.closeLocatePanel();
            } else {
                this.closeSearchPanel();
            }
        },
        filterClicked: function (e) {
            // show filter div
            if ($('.layers-selector-container').is(":hidden")) {
                this.resetAllControlState();
                this.openFilterPanel();
                this.closeSearchPanel();
                this.closeLocatePanel();
            } else {
                this.closeFilterPanel();
            }
        },
        locateClicked: function (e) {
            // show locate div
            if ($('.locate-options-container').is(":hidden")) {
                this.resetAllControlState();
                this.openLocatePanel();
                this.closeSearchPanel();
                this.closeFilterPanel();
            } else {
                this.closeLocatePanel();
            }
        },
        locationClicked: function (e) {
            var target = $(e.target);
            if (!target.hasClass('location-control')) {
                target = target.parent();
            }
            // Activate function
            if (!this.locationControlActive) {
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

            this.locateView = new LocateView({
                parent: this,
            });
            this.$el.append(this.locateView.render().$el);
            this.$el.append(this.dataDownloaderControl.render().$el);
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
        },
        closeSubFilter: function (e) {
            var target = $(e.target);
            target.parent().next().toggle();
            target.children('.filter-icon-arrow').toggle();
        },
        openFilterPanel: function () {
            this.$el.find('.filter-control').addClass('control-panel-selected');
            $('.layers-selector-container').show();
        },
        closeFilterPanel: function () {
            this.$el.find('.filter-control').removeClass('control-panel-selected');
            $('.layers-selector-container').hide();
        },
        openLocatePanel: function () {
            this.$el.find('.locate-control').addClass('control-panel-selected');
            $('.locate-options-container').show();
        },
        closeLocatePanel: function () {
            this.$el.find('.locate-control').removeClass('control-panel-selected');
            $('.locate-options-container').hide();
        },
        openLocateCoordinates: function (e) {
            this.closeLocatePanel();
            this.locateView.showModal();
        }

    })
});
