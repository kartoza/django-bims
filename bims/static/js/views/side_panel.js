define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        template: _.template($('#side-panel-template').html()),
        className: 'panel-wrapper',
        rightPanel: null,
        returnButton: null,
        events: {
            'click .close-panel': 'closeSidePanel'
        },
        initialize: function () {
            // Events
            Shared.Dispatcher.on('sidePanel:openSidePanel', this.openSidePanel, this);
            Shared.Dispatcher.on('sidePanel:closeSidePanel', this.closeSidePanel, this);
            Shared.Dispatcher.on('sidePanel:updateSidePanelHtml', this.updateSidePanelHtml, this);
            Shared.Dispatcher.on('sidePanel:fillSidePanelHtml', this.fillSidePanelHtml, this);
            Shared.Dispatcher.on('sidePanel:updateSidePanelTitle', this.updateSidePanelTitle, this);
            Shared.Dispatcher.on('sidePanel:appendSidePanelContent', this.appendSidePanelContent, this);

            Shared.Dispatcher.on('sidePanel:addEventToReturnButton', this.addEventToReturnButton, this);
            Shared.Dispatcher.on('sidePanel:showReturnButton', this.showReturnButton, this);
            Shared.Dispatcher.on('sidePanel:hideReturnButton', this.hideReturnButton, this);
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
        isSidePanelOpen: function () {
            return this.rightPanel.is(":visible");
        },
        openSidePanel: function (properties) {
            this.hideReturnButton();
            $('#geocontext-information-container').hide();
            this.rightPanel.show('slide', {direction: 'right'}, 200);
            if (typeof properties !== 'undefined') {
                this.clearSidePanel();
                this.$el.find('.panel-loading').show();
                this.updateSidePanelTitle('<i class="fa fa-map-marker"></i> ' + properties['name'] + '</span>');
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
            $('.side-panel-info').css("padding-top", $('.right-panel-header').outerHeight());
        },
        closeSidePanelAnimation: function () {
            var self = this;
            this.rightPanel.hide('slide', {direction: 'right'}, 200, function () {
                self.clearSidePanel();
            });
        },
        closeSidePanel: function (e) {
            Shared.Dispatcher.trigger('searchResult:clicked', null);
            Shared.Router.clearSearch();
            this.closeSidePanelAnimation();
            this.hideReturnButton();
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
        }
    })
});
