define(
    ['backbone', 'underscore', 'jquery', 'ol', 'views/search', 'views/locate', 'views/upload_data'],
    function (Backbone, _, $, ol, SearchView, LocateView, UploadDataView) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        locationControlActive: false,
        searchView: null,
        locateView: null,
        events: {
            'click .search-control': 'searchClicked',
            'click .filter-control': 'filterClicked',
            'click .locate-control': 'locateClicked',
            'click .upload-data': 'uploadDataClicked',
            'click .map-search-close': 'closeSearchPanel',
            'click .layers-selector-container-close': 'closeFilterPanel',
            'click .locate-options-container-close': 'closeLocatePanel',
            'click .sub-filter': 'closeSubFilter',
            'click .locate-coordinates': 'openLocateCoordinates',
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
        },
        searchClicked: function (e) {
            $('.layer-switcher.shown button').click();
            // show search div
            this.closeAllPanel();

            if (!this.searchView.isOpen()) {
                this.openSearchPanel();
            }
        },
        filterClicked: function (e) {
            $('.layer-switcher.shown button').click();
            this.closeAllPanel();
            // show filter div
            if ($('.layers-selector-container').is(":hidden")) {
                this.openFilterPanel();
            }
        },
        locateClicked: function (e) {
            $('.layer-switcher.shown button').click();
            this.closeAllPanel();
            // show locate div
            if ($('.locate-options-container').is(":hidden")) {
                this.openLocatePanel();
            }
        },
        uploadDataClicked: function (e) {
            this.closeAllPanel();
            var active = this.controlPanelClicked(e);
            this.parent.uploadDataState = active;
        },
        showUploadDataModal: function (lon, lat) {
            this.uploadDataView.showModal();
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

            this.uploadDataView = new UploadDataView({
                parent: this,
            });
            this.$el.append(this.uploadDataView.render().$el);

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
        controlPanelClicked: function (e) {
            var target = $(e.target);
            if (!target.hasClass('sub-control-panel')) {
                target = target.parent();
            }
            // Activate function
            if (!target.hasClass('control-panel-selected')) {
                target.addClass('control-panel-selected');
                return true;
            } else {
                target.removeClass('control-panel-selected');
                return false;
            }
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
        }, 
        closeAllPanel: function () {
            this.closeFilterPanel();
            this.closeLocatePanel();
            this.closeSearchPanel();

            var uploadDataElm = this.$el.find('.upload-data');
            if(uploadDataElm.hasClass('control-panel-selected')) {
                uploadDataElm.removeClass('control-panel-selected');
                this.parent.uploadDataState = false;
            }
        }

    })
});
