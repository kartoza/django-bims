define(['backbone', 'underscore'], function (Backbone, _) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        searchBox: null,
        searchBoxOpen: false,
        events: {
            'click .search-control': 'searchClicked',
            'click .filter-control': 'filterClicked',
            'click .location-control': 'locationClicked',
            'click .map-search-close': 'searchCloseClicked',
            'keypress #search': 'searchEnter'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
        },
        searchEnter: function (e) {
            if(e.which === 13) {
                let searchValue = $(e.target).val();
                if(searchValue.length < 3) {
                    console.log('Minimal 3 characters');
                    return false;
                }
                // Do search
                console.log(searchValue);
            }
        },
        searchClicked: function (e) {
            // show search div
            if(!this.searchBoxOpen) {
                this.$el.find('.search-control').addClass('control-panel-selected');
                this.searchBox.show();
                this.$el.find('#search').focus();
                this.searchBoxOpen = true;
            } else {
                this.$el.find('.search-control').removeClass('control-panel-selected');
                this.searchBox.hide();
                this.searchBoxOpen = false;
            }
        },
        searchCloseClicked: function (e) {
            this.searchBox.hide();
        },
        filterClicked: function (e) {
        },
        locationClicked: function (e) {
        },
        render: function () {
            this.$el.html(this.template());
            this.searchBox = this.$el.find('.map-search-box');
            this.searchBox.hide();
            return this;
        }
    })
});
