define(
    ['backbone', 'underscore', 'jquery', 'ol', 'views/search', 'views/locate', 'views/upload_data', 'views/data_downloader', 'views/geonode_layer'],
    function (Backbone, _, $, ol, SearchView, LocateView, UploadDataView, DataDownloader, GeonodeLayer) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        locationControlActive: false,
        uploadDataActive: false,
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
            this.dataDownloaderControl = new DataDownloader({
                 parent: this
             });
            this.geonodeLayerControl = new GeonodeLayer({
                 parent: this
             });
        },
        searchClicked: function (e) {
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
            if ($('.locate-options-container').is(":hidden")) {
                 this.resetAllControlState();
                 this.openLocatePanel();
                 this.closeSearchPanel();
                 this.closeFilterPanel();
            } else {
                this.closeLocatePanel();
            }
        },
        uploadDataClicked: function (e) {

            var button = $(this.$el.find('.upload-data')[0]);
            if(this.uploadDataActive) {
                button.removeClass('control-panel-selected');
                $('#footer-message span').html('-');
                $('#footer-message').hide();
            } else {
                this.resetAllControlState();
                button.addClass('control-panel-selected');
                $('#footer-message span').html('CLICK LOCATION ON THE MAP');
                $('#footer-message').show();
            }
            this.uploadDataActive = !this.uploadDataActive;
            this.parent.uploadDataState = this.uploadDataActive;
        },
        showUploadDataModal: function (lon, lat, siteFeature) {
            this.uploadDataView.showModal(lon, lat, siteFeature);
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
            this.uploadDataView = new UploadDataView({
                parent: this,
                map: this.parent.map
            });
            this.$el.append(this.uploadDataView.render().$el);

            this.$el.append(this.geonodeLayerControl.render().$el);

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
        resetAllControlState: function () {
            var uploadDataElm = this.$el.find('.upload-data');
            if(uploadDataElm.hasClass('control-panel-selected')) {
                uploadDataElm.removeClass('control-panel-selected');
                this.uploadDataActive = false;
                $('#footer-message span').html('-');
                $('#footer-message').hide();
                this.parent.uploadDataState = false;
            }

            $('.layer-switcher.shown button').click();
            $('.map-control-panel-box:visible').hide();
            $('.sub-control-panel.control-panel-selected').removeClass('control-panel-selected');
        }
    })
});
