define(
    [
        'backbone',
        'underscore',
        'shared',
        'jquery',
        'ol',
        'htmlToCanvas',
        'fileSaver',
        'views/search',
        'views/locate',
        'views/upload_data',
        'views/data_downloader-modal',
        'views/spatial_filter'],
    function (Backbone, _, Shared, $, ol, htmlToCanvas, fileSaver, SearchView, LocateView, UploadDataView, DataDownloader, SpatialFilter) {
        return Backbone.View.extend({
            template: _.template($('#map-control-panel').html()),
            locationControlActive: false,
            uploadDataActive: false,
            catchmentAreaActive: false,
            searchView: null,
            locateView: null,
            closedPopover: [],
            validateDataListOpen: false,
            events: {
                'click .search-control': 'searchClicked',
                'click .filter-control': 'filterClicked',
                'click .locate-control': 'locateClicked',
                'click .upload-data': 'uploadDataClicked',
                'click .download-control': 'downloadControlClicked',
                'click .map-search-close': 'closeSearchPanel',
                'click .spatial-filter-container-close': 'closeSpatialFilterPanel',
                'click .layers-selector-container-close': 'closeFilterPanel',
                'click .locate-options-container-close': 'closeLocatePanel',
                'click .sub-filter': 'closeSubFilter',
                'click .locate-coordinates': 'openLocateCoordinates',
                'click .locate-farm': 'openLocateFarm',
                'click .spatial-filter': 'spatialFilterClicked',
                'click .validate-data': 'validateDataClicked',
            },
            initialize: function (options) {
                _.bindAll(this, 'render');
                this.parent = options.parent;
                this.dataDownloaderControl = new DataDownloader({
                    parent: this
                });
                this.validateDataListOpen = false;
                Shared.Dispatcher.on('mapControlPanel:clickSpatialFilter', this.spatialFilterClicked, this);
                Shared.Dispatcher.on('mapControlPanel:validationClosed', this.validationDataClosed, this);
            },
            addPanel: function (elm) {
                elm.addClass('sub-control-panel');
                var mapControlPanel = this.$el.find('.map-control-panel');
                mapControlPanel.append(elm);
            },
            hidePopOver: function (elm) {
                if (!elm.hasClass('sub-control-panel')) {
                    elm = elm.parent();
                }
                for (var i=0; i<this.closedPopover.length; i++) {
                    this.closedPopover[i].popover('enable');
                    this.closedPopover[i].splice(i, 1);
                }
                elm.popover('hide');
                this.closedPopover.push(elm);
            },
            spatialFilterClicked: function (e) {
                if (!this.spatialFilter.isOpen()) {
                    this.hidePopOver($(e.target));
                    this.resetAllControlState();
                    this.openSpatialFilterPanel();
                    this.closeSearchPanel();
                    this.closeFilterPanel();
                    this.closeLocatePanel();
                    this.closeValidateData();
                } else {
                    this.closeSpatialFilterPanel();
                }
            },
            validateDataClicked: function (e) {
                if(!this.validateDataListOpen) {
                    this.hidePopOver($(e.target));
                    this.resetAllControlState();
                    this.closeSpatialFilterPanel();
                    this.closeSearchPanel();
                    this.closeFilterPanel();
                    this.closeLocatePanel();
                    this.openValidateData();
                } else {
                    this.closeValidateData();
                }
            },
            searchClicked: function (e) {
                if (!this.searchView.isOpen()) {
                    this.hidePopOver($(e.target));
                    this.resetAllControlState();
                    this.openSearchPanel();
                    this.closeFilterPanel();
                    this.closeLocatePanel();
                    this.closeSpatialFilterPanel();
                    this.closeValidateData();
                } else {
                    this.closeSearchPanel();
                }
            },
            filterClicked: function (e) {
                if ($('.layers-selector-container').is(":hidden")) {
                    this.hidePopOver($(e.target));
                    this.resetAllControlState();
                    this.openFilterPanel();
                    this.closeSearchPanel();
                    this.closeLocatePanel();
                    this.closeSpatialFilterPanel();
                    this.closeValidateData();
                } else {
                    this.closeFilterPanel();
                }
            },
            locateClicked: function (e) {
                if ($('.locate-options-container').is(":hidden")) {
                    this.hidePopOver($(e.target));
                    this.resetAllControlState();
                    this.openLocatePanel();
                    this.closeSearchPanel();
                    this.closeFilterPanel();
                    this.closeSpatialFilterPanel();
                    this.closeValidateData();
                } else {
                    this.closeLocatePanel();
                }
            },
            uploadDataClicked: function (e) {
                var button = $(this.$el.find('.upload-data')[0]);
                if (this.uploadDataActive) {
                    button.removeClass('control-panel-selected');
                    $('#footer-message span').html('-');
                    $('#footer-message').hide();
                } else {
                    this.hidePopOver($(e.target));
                    this.resetAllControlState();
                    button.addClass('control-panel-selected');
                    $('#footer-message span').html('CLICK LOCATION ON THE MAP');
                    $('#footer-message').show();
                }
                this.uploadDataActive = !this.uploadDataActive;
                this.parent.uploadDataState = this.uploadDataActive;
            },
            downloadControlClicked: function (e) {
                var button = $(e.target);
                if (!button.hasClass('sub-control-panel')) {
                    button = button.parent();
                }
                if (!button.hasClass('control-panel-selected')) {
                    this.resetAllControlState();
                    button.addClass('control-panel-selected');
                    this.dataDownloaderControl.showModal();
                } else {
                    button.removeClass('control-panel-selected');
                    $('#download-control-modal').hide();
                }
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
                this.$el.append(
                    this.dataDownloaderControl.render().$el);
                this.uploadDataView = new UploadDataView({
                    parent: this,
                    map: this.parent.map
                });
                this.$el.append(this.uploadDataView.render().$el);

                this.spatialFilter = new SpatialFilter({
                    parent: this,
                });

                this.$el.append(this.spatialFilter.render().$el);

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
            openSpatialFilterPanel: function () {
                this.$el.find('.spatial-filter').addClass('control-panel-selected');
                this.spatialFilter.show();
            },
            closeSpatialFilterPanel: function () {
                this.$el.find('.spatial-filter').removeClass('control-panel-selected');
                this.spatialFilter.hide();
            },
            closeValidateData: function () {
                this.$el.find('.validate-data').removeClass('control-panel-selected');
                Shared.Dispatcher.trigger('sidePanel:closeValidateDataList');
                this.validateDataListOpen = false;
            },
            validationDataClosed: function () {
                this.$el.find('.validate-data').removeClass('control-panel-selected');
                this.validateDataListOpen = false;
            },
            openValidateData: function () {
                this.$el.find('.validate-data').addClass('control-panel-selected');
                Shared.Dispatcher.trigger('sidePanel:openValidateDataList');
                this.validateDataListOpen = true;
            },
            closeSubFilter: function (e) {
                var target = $(e.target);
                var $wrapper = target.closest('.sub-filter');
                $wrapper.next().toggle();
                $wrapper.find('.filter-icon-arrow').toggle();
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
                this.locateView.showModal('.coordinate-form');
            },
            openLocateFarm: function (e) {
                this.closeLocatePanel();
                this.locateView.showModal('.farm-form');
            },
            resetAllControlState: function () {
                $('#download-control-modal').hide();
                var uploadDataElm = this.$el.find('.upload-data');
                if (uploadDataElm.hasClass('control-panel-selected')) {
                    uploadDataElm.removeClass('control-panel-selected');
                    this.uploadDataActive = false;
                    $('#footer-message span').html('-');
                    $('#footer-message').hide();
                    this.parent.uploadDataState = false;
                }
                Shared.Dispatcher.trigger('sidePanel:closeValidateDataList');

                $('.layer-switcher.shown button').click();
                $('.map-control-panel-box:visible').hide();
                $('.sub-control-panel.control-panel-selected').removeClass('control-panel-selected');
            }
        })
    });
