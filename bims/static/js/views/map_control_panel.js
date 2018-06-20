define(['backbone', 'underscore', 'jquery', 'ol'], function (Backbone, _, $, ol) {
    return Backbone.View.extend({
        template: _.template($('#map-control-panel').html()),
        searchBox: null,
        searchBoxOpen: false,
        locationControlActive: false,
        searchResults: {},
        events: {
            'click .search-control': 'searchClicked',
            'click .filter-control': 'filterClicked',
            'click .location-control': 'locationClicked',
            'click .map-search-close': 'closeSearchPanel',
            'click .result-search': 'searchResultClicked',
            'keypress #search': 'searchEnter'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
        },
        searchResultClicked: function (e) {
            var id = $(e.target).data('search-result-id');
            if(typeof id === "undefined") {
                return false;
            }

            var searchResult = this.searchResults[id];
            var geometry = JSON.parse(searchResult['geometry']);
            this.parent.map.getView().setCenter(ol.proj.transform(geometry['coordinates'],"EPSG:4326",  "EPSG:3857"));
            this.parent.map.getView().setZoom(15);
        },
        searchEnter: function (e) {
            var self = this;
            if(e.which === 13) {
                $('#search-results-wrapper').html('');
                var searchValue = $(e.target).val();
                if(searchValue.length < 3) {
                    console.log('Minimal 3 characters');
                    $('#search-results-wrapper').html('Minimal 3 characters');
                    return false;
                }

                $.ajax({
                    type: 'GET',
                    url: '/api/search/' + searchValue + '/',
                    success: function (data) {
                        self.searchResults = {};
                        if (data['results']) {
                            $('#search-results-wrapper').html(data['results'])
                        } else {
                            $.each(data, function (key, value) {
                                self.searchResults[value['id']] = value;
                                $('#search-results-wrapper').append(
                                    '<div class="result-search" data-search-result-id="' + value['id'] + '" >' +
                                    '<span>Original species name: ' + value['original_species_name'] + '</span><br/>' +
                                    '<span>Collector: ' + value['collector'] + '</span><br/>' +
                                    '<span>Collection Date: ' + value['collection_date'] + '</span>' +
                                    '<div/>'
                                )

                            });
                        }
                    }
                })
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
