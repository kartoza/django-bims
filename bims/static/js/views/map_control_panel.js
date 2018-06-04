define(['backbone', 'underscore'], function (Backbone, _) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        searchBox: null,
        searchBoxOpen: false,
        locationControlActive: false,
        events: {
            'click .search-control': 'searchClicked',
            'click .filter-control': 'filterClicked',
            'click .location-control': 'locationClicked',
            'click .map-search-close': 'closeSearchPanel',
            'keypress #search': 'searchEnter'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
        },
        searchEnter: function (e) {
            if(e.which === 13) {
                var searchValue = $(e.target).val();
                if(searchValue.length < 3) {
                    console.log('Minimal 3 characters');
                    return false;
                }
                // Do search
            }
        },
        searchClicked: function (e) {
            // show search div
            if(!this.searchBoxOpen) {
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
            this.searchBox = this.$el.find('.map-search-box');
            this.searchBox.hide();
            return this;
        },
        openSearchPanel: function () {
            this.$el.find('.search-control').addClass('control-panel-selected');
            this.searchBox.show();
            this.$el.find('#search').focus();
            this.searchBoxOpen = true;
        },
        closeSearchPanel: function () {
            this.$el.find('.search-control').removeClass('control-panel-selected');
            this.searchBox.hide();
            this.searchBoxOpen = false;
        },
        closeAllPanel: function () {
            this.closeSearchPanel();
        }
    })
});
