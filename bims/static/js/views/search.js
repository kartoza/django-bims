
define(['backbone', 'underscore', 'shared', 'ol'], function (Backbone, _, Shared, ol) {

    return Backbone.View.extend({
        template: _.template($('#map-search-container').html()),
        searchBox: null,
        searchBoxOpen: false,
        searchResults: {},
        events: {
            'keypress #search': 'searchEnter',
            'click .result-search': 'searchResultClicked',
        },
        searchEnter: function (e) {
            var self = this;
            if(e.which === 13) {
                $('#search-results-wrapper').html('');
                var searchValue = $(e.target).val();
                if(searchValue.length < 3) {
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
        searchResultClicked: function (e) {
            var id = $(e.target).data('search-result-id');
            if(typeof id === "undefined") {
                return false;
            }

            var searchResult = this.searchResults[id];
            var geometry = JSON.parse(searchResult['geometry']);
            var coordinates = ol.proj.transform(geometry['coordinates'], "EPSG:4326", "EPSG:3857");
            var zoomLevel = 15;
            Shared.Dispatcher.trigger('map:zoomToCoordinates', coordinates, zoomLevel);

        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
        },
        render: function () {
            this.$el.html(this.template());
            this.searchBox = this.$el.find('.map-search-box');
            this.searchBox.hide();
            return this;
        },
        show: function () {
            this.searchBox.show();
            this.$el.find('#search').focus();
            this.searchBoxOpen = true;
        },
        hide: function () {
            this.searchBox.hide();
            this.searchBoxOpen = false;
        },
        isOpen: function () {
            return this.searchBoxOpen;
        }
    })

});