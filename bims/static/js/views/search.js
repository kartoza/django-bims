define(['backbone', 'underscore', 'shared', 'ol', 'noUiSlider', 'collections/search_result'], function (Backbone, _, Shared, ol, NoUiSlider, SearchResultCollection) {

    return Backbone.View.extend({
        template: _.template($('#map-search-container').html()),
        searchBox: null,
        searchBoxOpen: false,
        searchResults: {},
        events: {
            'keypress #search': 'searchEnter',
            'click .search-arrow': 'searchClick',
            'click .apply-filter': 'searchClick',
            'click .clear-filter': 'clearFilter'
        },
        search: function (searchValue) {
            var self = this;
            this.sidePanel.openSidePanel();
            this.sidePanel.clearSidePanel();

            $('#search-results-wrapper').html('');

            var collectorValue = [];
            $('input[name=collector-value]:checked').each(function () {
                collectorValue.push($(this).val())
            });
            if (collectorValue.length === 0) {
                collectorValue = ''
            } else {
                var encodedCollectorValue = [];
                $.each(collectorValue, function (index, value) {
                    encodedCollectorValue.push(encodeURIComponent(value));
                });
                collectorValue = encodeURIComponent(JSON.stringify(
                    collectorValue)
                );
            }

            var categoryValue = [];
            $('input[name=category-value]:checked').each(function () {
                categoryValue.push($(this).val())
            });
            if (categoryValue.length === 0) {
                categoryValue = ''
            } else {
                categoryValue = JSON.stringify(categoryValue)
            }
            var parameters = {
                'search': searchValue,
                'collector': collectorValue,
                'category': categoryValue,
                'yearFrom': '',
                'yearTo': '',
                'months': ''
            };
            var yearFrom = $('#year-from').html();
            var yearTo = $('#year-to').html();
            var monthSelected = [];
            if ($('#month-selector').find('input:checkbox:checked').length > 0 ||
                yearFrom != this.startYear || yearTo != this.endYear) {
                $('#month-selector').find('input:checkbox:checked').each(function () {
                    monthSelected.push($(this).val());
                });
                parameters['yearFrom'] = yearFrom;
                parameters['yearTo'] = yearTo;
                parameters['months'] = monthSelected.join(',');
            }
            Shared.Dispatcher.trigger('map:closeHighlight');
            Shared.Dispatcher.trigger('search:hit', parameters);
            if (!parameters['search']
                && !parameters['collector']
                && !parameters['category']
                && !parameters['yearFrom']
                && !parameters['yearTo']) {
                return false
            }
            this.searchResultCollection.search(
                this.sidePanel, parameters
            );
            this.searchResultCollection.fetch({
                success: function () {
                    self.searchResultCollection.renderCollection()
                }
            });
        },
        searchClick: function () {
            var searchValue = $('#search').val();
            Shared.Router.clearSearch();
            this.search(searchValue);
        },
        searchEnter: function (e) {
            if (e.which === 13) {
                var searchValue = $('#search').val();
                Shared.Router.clearSearch();
                this.search(searchValue);
            }
        },
        datePickerToDate: function (element) {
            if ($(element).val()) {
                return new Date($(element).val().replace(/(\d{2})-(\d{2})-(\d{4})/, "$2/$1/$3")).getTime()
            } else {
                return '';
            }
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.sidePanel = options.sidePanel;
            this.searchResultCollection = new SearchResultCollection();
            Shared.Dispatcher.on('search:searchCollection', this.search, this);
        },
        render: function () {
            this.$el.html(this.template());
            this.searchBox = this.$el.find('.map-search-box');
            this.searchBox.hide();
            return this;
        },
        initDateFilter: function () {
            // render slider
            this.startYear = parseInt(min_year_filter);
            this.endYear = parseInt(max_year_filter);
            this.yearSlider = NoUiSlider.create($('#year-slider')[0], {
                start: [this.startYear, this.endYear],
                connect: true,
                range: {
                    'min': this.startYear,
                    'max': this.endYear
                },
                step: 1
            });
            $('#year-from').html(this.startYear);
            $('#year-to').html(this.endYear);
            this.yearSlider.on('slide', function doSomething(values, handle, unencoded, tap, positions) {
                $('#year-from').html(Math.floor(values[0]));
                $('#year-to').html(Math.floor(values[1]));
            });

            // create month selector
            var monthSelectorHtml = '';
            var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            $.each(months, function (index, value) {
                if (index % 4 == 0) {
                    monthSelectorHtml += '<tr>';
                }
                monthSelectorHtml += '<td><input type="checkbox" value="' + (index + 1) + '">' + value + '</td>';
                if (index % 4 == 3) {
                    monthSelectorHtml += '</tr>';
                }
            });
            $('#month-selector').html(monthSelectorHtml);
        },
        clearFilter: function (e) {
            var target = $(e.target);
            target.closest('.row').find('input:checkbox:checked').prop('checked', false);
            if (target.closest('.row').find('#year-from').length > 0) {
                this.yearSlider.set([this.startYear, this.endYear]);
                target.closest('.row').find('#year-from').html(this.startYear);
                target.closest('.row').find('#year-to').html(this.endYear);
            }
            this.searchClick();

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