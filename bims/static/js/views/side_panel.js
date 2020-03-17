define(['shared', 'backbone', 'underscore', 'jqueryUi', 'jquery', 'views/right_panel/validate_data_list'], function (Shared, Backbone, _, JqueryUI, $, ValidateDataListView) {
    return Backbone.View.extend({
        template: _.template($('#side-panel-template').html()),
        className: 'panel-wrapper',
        rightPanel: null,
        returnButton: null,
        validationMode: false,
        siteDetailData: null,
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        events: {
            'click .close-panel': 'closeSidePanel',
            'click .open-detailed-site-button' : 'openDetailedSiteButton',
            'click .open-fish-detailed-site-button' : 'openFishDetailedSiteButton',
            'click #rp-view-fish-form': 'openFishPanel',
            'click #rp-add-sass': 'addSassPanel',
            'click #rp-view-sass': 'viewSassPanel'
        },
        initialize: function () {
            // Events
            Shared.Dispatcher.on('sidePanel:openSidePanel', this.openSidePanel, this);
            Shared.Dispatcher.on('sidePanel:closeSidePanel', this.closeSidePanel, this);
            Shared.Dispatcher.on('sidePanel:clearSidePanel', this.clearSidePanel, this);
            Shared.Dispatcher.on('sidePanel:updateSidePanelHtml', this.updateSidePanelHtml, this);
            Shared.Dispatcher.on('sidePanel:fillSidePanelHtml', this.fillSidePanelHtml, this);
            Shared.Dispatcher.on('sidePanel:addContentWithTab', this.addContentWithTab, this);
            Shared.Dispatcher.on('sidePanel:updateSidePanelTitle', this.updateSidePanelTitle, this);
            Shared.Dispatcher.on('sidePanel:appendSidePanelContent', this.appendSidePanelContent, this);

            Shared.Dispatcher.on('sidePanel:addEventToReturnButton', this.addEventToReturnButton, this);
            Shared.Dispatcher.on('sidePanel:showReturnButton', this.showReturnButton, this);
            Shared.Dispatcher.on('sidePanel:hideReturnButton', this.hideReturnButton, this);

            Shared.Dispatcher.on('sidePanel:openValidateDataList', this.openValidateDataList, this);
            Shared.Dispatcher.on('sidePanel:closeValidateDataList', this.closeValidateDataList, this);
            Shared.Dispatcher.on('sidePanel:updateSiteDetailData', this.updateSiteDetailData, this);

            this.validateDataListView = new ValidateDataListView({
                parent: this
            });
        },
        render: function () {
            this.$el.html(this.template());
            // $('#map-container').append(this.$el);

            // Hide the side panel
            this.rightPanel = this.$el.find('.right-panel');
            this.returnButton = this.rightPanel.find('.return-panel');

            this.hideReturnButton();

            this.rightPanel.css('display', 'none');

            return this;
        },
        openValidateDataList: function () {
            this.clearSidePanel();
            this.openSidePanel();
            this.switchToSearchResultPanel();
            this.validateDataListView.delegateEvents();
            this.$el.find('#content-panel').append(this.validateDataListView.render().$el);
            this.validateDataListView.show();
            this.validationMode = true;
        },
        closeValidateDataList: function () {
            this.closeSidePanel();
            this.validateDataListView.close();
            this.validationMode = false;
        },
        isSidePanelOpen: function () {
            return this.rightPanel.is(":visible");
        },
        openSidePanel: function (properties) {
            if (this.validationMode) {
                Shared.Dispatcher.trigger('mapControlPanel:validationClosed');
                this.validationMode = false;
            }
            Shared.SidePanelOpen = true;
            Shared.Dispatcher.trigger('biodiversityLegend:moveLeft');
            Shared.Dispatcher.trigger('bugReport:moveLeft');
            this.hideReturnButton();
            $('#geocontext-information-container').hide();
            this.rightPanel.show('slide', {direction: 'right'}, 200);
            if (typeof properties !== 'undefined') {
                this.clearSidePanel();
                this.$el.find('.panel-loading').show();
                this.updateSidePanelTitle('<i class="fa fa-map-marker"></i>Overview</span>');
                if (properties.hasOwnProperty('location_type')) {
                    this.fillSidePanel(properties['location_type']);
                }
            }
        },
        showSearchLoading: function () {
            $('.panel-loading').show();
            $('.side-panel-info').removeClass('full-height');
        },
        switchToSearchResultPanel: function () {
            $('.panel-loading').hide();
            $('.title-side-panel').show();
            $('.search-result-info').show();
            $('.side-panel-info').addClass('full-height');
        },
        switchToDetailResultPanel: function () {
            $('.panel-loading').hide();
            $('.title-side-panel').hide();
            $('.search-result-info').hide();
            $('.side-panel-info').removeClass('full-height');
        },
        updateSidePanelTitle: function (title) {
            var $rightPanelTitle = this.$el.find('.right-panel-title');
            $rightPanelTitle.html(title);
            $('.side-panel-info').css("padding-top", '3rem');
        },
        closeSidePanelAnimation: function () {
            var self = this;
            this.rightPanel.hide('slide', {direction: 'right'}, 200, function () {
                self.clearSidePanel();
            });
        },
        closeSidePanel: function (e) {
            Shared.Dispatcher.trigger('searchResult:clicked', null);
            Shared.Dispatcher.trigger('biodiversityLegend:moveRight');
            Shared.Dispatcher.trigger('bugReport:moveRight');
            Shared.Dispatcher.trigger('siteDetail:panelClosed');
            Shared.SidePanelOpen = false;
            this.closeSidePanelAnimation();
            this.hideReturnButton();
            if (this.validationMode) {
                Shared.Dispatcher.trigger('mapControlPanel:validationClosed');
                this.validationMode = false;
            }
        },
        fillSidePanel: function (contents) {
            for (var key in contents) {
                if (contents.hasOwnProperty(key)) {
                    $('#content-panel').append('<p>' + key.charAt(0).toUpperCase() + key.substring(1) + ' : ' + contents[key] + '</p>');
                }
            }
        },
        fillSidePanelHtml: function (htmlData) {
            this.switchToSearchResultPanel();
            $('#content-panel').html(htmlData);
        },
        updateSidePanelHtml: function (htmlData) {
            this.switchToSearchResultPanel();
            $('#content-panel').append(htmlData);
        },
        appendSidePanelContent: function (htmlData) {
            $('#content-panel').append(htmlData);
        },
        addContentWithTab: function (title, contentData) {
            const tabPanelTemplate = _.template($('#tab-panel-template').html());
            $('#content-panel').append(tabPanelTemplate({
                'titleName': title,
                'content': contentData
            }));
        },
        clearSidePanel: function () {
            $('#content-panel').html('');
            $('.panel-icons').html('');
            this.updateSidePanelTitle('');
        },
        addEventToReturnButton: function (eventFunction) {
            this.returnButton.on('click', eventFunction);
        },
        clearReturnButtonFunction: function () {
            this.returnButton.off();
        },
        showReturnButton: function () {
            this.clearReturnButtonFunction();
            this.returnButton.show();
        },
        hideReturnButton: function () {
            this.clearReturnButtonFunction();
            this.returnButton.hide();
        },
        updateSiteDetailData: function (siteDetailData) {
            this.siteDetailData = siteDetailData;
        },
        openDetailedSiteButton: function () {
            if (this.siteDetailData) {
                Shared.Dispatcher.trigger('map:showSiteDetailedDashboard', this.siteDetailData);
            }
        },
        openFishDetailedSiteButton: function () {
            filterParameters['modules'] = Shared.FishModuleID;
            if (this.siteDetailData) {
                Shared.Dispatcher.trigger('map:showSiteDetailedDashboard', this.siteDetailData);
            }
        },
        openFishPanel: function () {
            window.location.href = "/fish-form/?siteId=" + filterParameters['siteId'];
        },
        addSassPanel: function () {
            window.location.href = "/sass/" + filterParameters['siteId'];
        },
        viewSassPanel: function () {
            window.location.href = "/sass/dashboard/" + filterParameters['siteId'] + '/' + this.apiParameters(filterParameters);
        }
    })
});
