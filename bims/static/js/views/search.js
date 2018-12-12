define([
    'backbone',
    'underscore',
    'shared',
    'ol',
    'noUiSlider',
    'collections/search_result',
    'views/search_panel',
    'jquery',
    'views/filter_panel/reference_category',
    'views/filter_panel/spatial_filter'
], function (Backbone, _, Shared, ol, NoUiSlider, SearchResultCollection, SearchPanelView, $,
             ReferenceCategoryView, SpatialFilterView) {

    return Backbone.View.extend({
        template: _.template($('#map-search-container').html()),
        searchBox: null,
        searchBoxOpen: false,
        searchResults: {},
        events: {
            'keyup #search': 'checkSearch',
            'keypress #search': 'searchEnter',
            'click .search-arrow': 'searchClick',
            'click .apply-filter': 'searchClick',
            'click .clear-filter': 'clearFilter',
            'click .search-reset': 'clearSearch',
            'click .origin-btn': 'handleOriginBtnClick',
            'click .endemic-dropdown-item': 'handleEndemicDropdown',
            'click .clear-origin-filter': 'handleClearOriginClicked'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.sidePanel = options.sidePanel;
            this.searchPanel = new SearchPanelView();
            this.searchResultCollection = new SearchResultCollection();
            Shared.Dispatcher.on('search:searchCollection', this.search, this);
            Shared.Dispatcher.on('search:doSearch', this.searchClick, this);
            Shared.Dispatcher.on('search:clearSearch', this.clearSearch, this);
            Shared.Dispatcher.on('search:checkSearchCollection', this.checkSearch, this);
        },
        render: function () {
            var self = this;
            this.$el.html(this.template());
            this.searchBox = this.$el.find('.map-search-box');
            this.searchInput = this.$el.find('#search');
            this.searchInput.autocomplete({
                autoFocus: true,
                source: function (request, response) {
                    $.ajax({
                        url: "/autocomplete/",
                        data: {q: request.term},
                        dataType: "json",
                        success: function (requestResponse) {
                            var responseData = [];
                            if (requestResponse.hasOwnProperty('results')) {
                                $.each(requestResponse['results'], function (index, value) {
                                    responseData.push({
                                        'value': value['name'],
                                        'label': value['name'],
                                        'id': value['id']
                                    })
                                })
                            }
                            response(responseData);
                        }
                    })
                },
                select: function (event, ui) {
                    var itemValue = ui['item']['value'];
                    self.search(itemValue);
                }
            });
            this.searchBox.hide();
            this.$el.append(this.searchPanel.render().$el);
            this.referenceCategoryView = new ReferenceCategoryView();
            this.$el.find('.reference-category-wrapper').append(this.referenceCategoryView.render().$el);

            this.spatialFilterView = new SpatialFilterView();
            this.$el.find('.spatial-filter-wrapper').append(this.spatialFilterView.render().$el);

            var nativeOriginDropdown = self.$el.find('.native-origin-dropdown');
            $.ajax({
                type: 'GET',
                url: '/api/endemism-list/',
                dataType: 'json',
                success: function (data) {
                    for (var i = 0; i < data.length; i++) {
                        nativeOriginDropdown.append(
                            '<div class="dropdown-item endemic-dropdown-item" data-endemic-value="' + data[i] + '">' +
                            ' <input class="endemic-checkbox" name="endemic-value" type="checkbox" value="' + data[i] + '"> ' + data[i] + '</div>'
                        )
                    }
                }
            });

            return this;
        },
        checkSearch: function (forceSearch) {
            var searchValue = $('#search').val();
            if (searchValue.length > 0 && searchValue.length < 3) {
                $('#search-error-text').show();
                $('.apply-filter').attr("disabled", "disabled");
                $('.search-arrow').addClass('disabled');
            } else {
                $('#search-error-text').hide();
                $('.apply-filter').removeAttr("disabled");
                $('.search-arrow').removeClass('disabled');
            }
            if (forceSearch === true) {
                this.search(searchValue);
            }
        },
        search: function (searchValue) {
            Shared.Dispatcher.trigger('siteDetail:updateCurrentSpeciesSearchResult', []);
            if ($('#search-error-text').is(":visible")) {
                return;
            }
            var self = this;
            this.searchPanel.clearSidePanel();
            this.searchPanel.openSidePanel(false);

            $('#search-results-wrapper').html('');

            // reference category
            var referenceCategory = self.referenceCategoryView.getSelected();
            if (referenceCategory.length > 0) {
                referenceCategory = JSON.stringify(referenceCategory);
            } else {
                referenceCategory = '';
            }

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

            // reference
            var referenceValue = [];
            $('input[name=reference-value]:checked').each(function () {
                referenceValue.push($(this).val())
            });
            if (referenceValue.length === 0) {
                referenceValue = ''
            } else {
                var encodedReferenceValue = [];
                $.each(referenceValue, function (index, value) {
                    encodedReferenceValue.push(encodeURIComponent(value));
                });
                referenceValue = encodeURIComponent(JSON.stringify(
                    referenceValue)
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

            var endemicValue = [];
            $('input[name=endemic-value]:checked').each(function () {
                endemicValue.push($(this).val())
            });
            if (endemicValue.length === 0) {
                endemicValue = ''
            } else {
                endemicValue = JSON.stringify(endemicValue)
            }

            var boundaryValue = [];
            // just get the top one.
            $('input[name=boundary-value]:checked').each(function () {
                boundaryValue.push($(this).val())
            });

            var userBoundarySelected = Shared.UserBoundarySelected;

            if (userBoundarySelected.length === 0 && boundaryValue.length === 0) {
                Shared.Dispatcher.trigger('map:boundaryEnabled', false);
                Shared.Dispatcher.trigger('map:closeHighlightPinned');
            } else {
                Shared.Dispatcher.trigger('map:boundaryEnabled', true);
            }

            if (boundaryValue.length > 0) {
                Shared.Dispatcher.trigger('catchmentArea:show-administrative', JSON.stringify(boundaryValue));
            }

            var parameters = {
                'search': searchValue,
                'collector': collectorValue,
                'category': categoryValue,
                'boundary': boundaryValue.length === 0 ? '' : JSON.stringify(boundaryValue),
                'userBoundary': userBoundarySelected.length === 0 ? '' : JSON.stringify(userBoundarySelected),
                'yearFrom': '',
                'yearTo': '',
                'months': '',
                'reference': referenceValue,
                'referenceCategory': referenceCategory,
                'endemic': endemicValue
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
            Shared.Dispatcher.trigger(Shared.EVENTS.SEARCH.HIT, parameters);
            Shared.Dispatcher.trigger('sidePanel:closeSidePanel');
            if (!parameters['search']
                && !parameters['collector']
                && !parameters['category']
                && !parameters['yearFrom']
                && !parameters['yearTo']
                && !parameters['userBoundary']
                && !parameters['referenceCategory']
                && !parameters['reference']
                && !parameters['endemic']
                && !parameters['boundary']) {
                Shared.Dispatcher.trigger('cluster:updateAdministrative', '');
                return false
            }
            this.searchResultCollection.search(
                this.searchPanel, parameters
            );
        },
        searchClick: function () {
            if (Shared.CurrentState.FETCH_CLUSTERS) {
                return true;
            }
            Shared.Dispatcher.trigger('map:clearAllLayers');
            var searchValue = $('#search').val();
            Shared.Router.clearSearch();
            this.search(searchValue);
        },
        searchEnter: function (e) {
            if (e.which === 13) {
                if (Shared.CurrentState.FETCH_CLUSTERS) {
                    return true;
                }
                var searchValue = $('#search').val();
                Shared.Router.clearSearch();
                this.search(searchValue);
            }
        },
        clearSearch: function () {
            Shared.CurrentState.SEARCH = false;
            this.searchInput.val('');
            $('.clear-filter').click();
            $('.map-search-result').hide();
            this.searchPanel.clearSidePanel();
            this.clearClickedOriginButton();

            Shared.Dispatcher.trigger('politicalRegion:clear');

            Shared.Dispatcher.trigger('spatialFilter:clearSelected');
            Shared.Dispatcher.trigger('siteDetail:updateCurrentSpeciesSearchResult', []);
            Shared.Dispatcher.trigger('cluster:updateAdministrative', '');
            Shared.Dispatcher.trigger('clusterBiological:clearClusters');

            Shared.Dispatcher.trigger('map:clearAllLayers');
            Shared.Dispatcher.trigger('map:refetchRecords');
        },
        datePickerToDate: function (element) {
            if ($(element).val()) {
                return new Date($(element).val().replace(/(\d{2})-(\d{2})-(\d{4})/, "$2/$1/$3")).getTime()
            } else {
                return '';
            }
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
            if (Shared.CurrentState.SEARCH) {
                this.searchClick();
            }
        },
        show: function () {
            this.searchBox.show();
            this.searchPanel.openSidePanel();
            this.$el.find('#search').focus();
            this.searchBoxOpen = true;
        },
        hide: function () {
            this.searchBox.hide();
            this.searchBoxOpen = false;
            this.searchPanel.hide();
        },
        isOpen: function () {
            return this.searchBoxOpen;
        },
        handleOriginBtnClick: function (e) {
            var target = $(e.target);
            if (target.hasClass('dropdown-toggle')) {
                return;
            }
            var origin = target.data('origin');
            if (target.hasClass('selected')) {
                $('#' + origin).prop('checked', false);
                target.removeClass('selected');
            } else {
                $('#' + origin).prop('checked', true);
                target.addClass('selected');
            }
        },
        handleEndemicDropdown: function (e) {
            e.stopPropagation();
            var endemicValue = $(e.target).data('endemic-value');
            var inputCheckbox = $(e.target).find('input');

            if (endemicValue === 'all-endemic') {
                if (inputCheckbox.is(":checked")) {
                    $('#indigenous').prop('checked', false);
                    inputCheckbox.prop('checked', false);
                } else {
                    $(e.target).parent().find('.endemic-checkbox').prop('checked', true);
                    $('#indigenous').prop('checked', true);
                    inputCheckbox.prop('checked', true);
                }
            } else {
                $('#all-endemic-checkbox').prop('checked', false);
                $('#indigenous').prop('checked', false);
                if (inputCheckbox.is(":checked")) {
                    inputCheckbox.prop('checked', false);
                } else {
                    inputCheckbox.prop('checked', true);
                }
            }

            var atLeastOneIsChecked = $('.native-origin-dropdown').find('.endemic-checkbox:checked').length > 0;
            if (atLeastOneIsChecked) {
                $('#native-origin-btn').addClass('selected');
            } else {
                $('#native-origin-btn').removeClass('selected');
            }
        },
        clearClickedOriginButton: function () {
            this.$el.find('.origin-btn').removeClass('selected');
        },
        handleClearOriginClicked: function (e) {
            this.clearClickedOriginButton();
        }
    })

});