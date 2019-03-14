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
        shouldUpdateUrl: true,
        searchResults: {},
        filtersReady: {
            'endemism': false,
            'collector': false,
            'study-reference': false,
            'referenceCategory': false
        },
        initialSelectedStudyReference: [],
        initialSelectedCollectors: [],
        initialSelectedReferenceCategory: [],
        initialSelectedEndemic: [],
        initialYearFrom: null,
        initialYearTo: null,
        events: {
            'keyup #search': 'checkSearch',
            'keypress #search': 'searchEnter',
            'click .search-arrow': 'searchClick',
            'click .apply-filter': 'searchClick',
            'click .clear-filter': 'clearFilter',
            'click .search-reset': 'clearSearch',
            'click .origin-btn': 'handleOriginBtnClick',
            'click .endemic-dropdown-item': 'handleEndemicDropdown',
            'click .clear-origin-filter': 'handleClearOriginClicked',
            'click .clear-conservation-filter': 'handleClearConservationClicked'
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
            Shared.Dispatcher.on('filters:updateFilters', this.filtersUpdated, this);
            Shared.Dispatcher.on('search:showMoreSites', this.showMoreSites, this);
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
                                        'value': value['suggested_name'],
                                        'label': value['suggested_name'],
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
            this.referenceCategoryView = new ReferenceCategoryView({parent: this});
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
                        var checked = '';
                        if ($.inArray(data[i], self.initialSelectedEndemic) > -1) {
                            checked = 'checked';
                        }
                        nativeOriginDropdown.append(
                            '<div class="dropdown-item endemic-dropdown-item" data-endemic-value="' + data[i] + '">' +
                            ' <input class="endemic-checkbox" name="endemic-value" type="checkbox" value="' + data[i] + '" ' + checked + '> ' + data[i] + '</div>'
                        )
                    }
                    self.filtersReady['endemism'] = true;
                }
            });

            $.ajax({
                type: 'GET',
                url: listCollectorAPIUrl,
                dataType: 'json',
                success: function (data) {
                    var selected;
                    for (var i = 0; i < data.length; i++) {
                        if ($.inArray(data[i], self.initialSelectedCollectors) > -1) {
                            selected = 'selected';
                        }
                        else {
                            selected = '';
                        }

                        if (data[i]) {
                            $('#filter-collectors').append(`
                                <option value="${data[i]}" ${selected}>${data[i]}</option>`);
                        }
                    }
                    self.filtersReady['collector'] = true;
                    $('#filter-collectors').chosen({});
                }
            });

            $.ajax({
                type: 'GET',
                url: listReferenceAPIUrl,
                dataType: 'json',
                success: function (data) {
                    if (data.length === 0) {
                        $('.study-reference-wrapper').hide();
                    } else {
                        var selected;
                        for (var i = 0; i < data.length; i++) {
                            if ($.inArray(data[i]['reference'], self.initialSelectedStudyReference) > -1) {
                                selected = 'selected';
                            }
                            else
                            {
                                selected = '';
                            }
                            if (data[i]) {
                                $('#filter-study-reference').append(`
                                    <option value="${data[i]['reference']}" ${selected}>${data[i]['reference']}</option>`);
                            }
                        }
                    }
                    self.filtersReady['study-reference'] = true;
                    $('#filter-study-reference').chosen({});
                }
            });

            return this;
        },
        isAllFiltersReady: function () {
            var isReady = true;
            $.each(this.filtersReady, function (key, ready) {
                if (!ready) {
                    isReady = false;
                    return false;
                }
            });
            return isReady;
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
                if (!this.isAllFiltersReady()) {
                    var that = this;
                    setTimeout(function () {
                        that.checkSearch(forceSearch);
                    }, 500);
                    return false;
                }
                this.search(searchValue);
            }
        },
        getSelectedConservationStatus: function () {
            var status = this.$el.find("#conservation-status").chosen().val();
            if (status) {
                return JSON.stringify(status)
            }
            return '';
        },
        clearSelectedConservationStatus: function () {
            return this.$el.find("#conservation-status").val("").trigger('chosen:updated');
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

            var collectorValue = $("#filter-collectors").val();
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
            var referenceValue = $("#filter-study-reference").val();
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

            var conservationStatusValue = this.getSelectedConservationStatus();

            var boundaryValue = this.spatialFilterView.selectedPoliticalRegions;

            var userBoundarySelected = Shared.UserBoundarySelected;
            if (userBoundarySelected.length === 0 && boundaryValue.length === 0) {
                Shared.Dispatcher.trigger('map:boundaryEnabled', false);
                Shared.Dispatcher.trigger('map:closeHighlightPinned');
            } else {
                Shared.Dispatcher.trigger('map:boundaryEnabled', true);
            }

            if (boundaryValue.length > 0) {
                Shared.Dispatcher.trigger('catchmentArea:show-administrative', boundaryValue);
            }

            var spatialFilters = this.spatialFilterView.selectedSpatialFilters;

            var parameters = {
                'search': searchValue,
                'collector': collectorValue,
                'category': categoryValue,
                'boundary': boundaryValue.length === 0 ? '' : JSON.stringify(boundaryValue),
                'userBoundary': userBoundarySelected.length === 0 ? '' : JSON.stringify(userBoundarySelected),
                'yearFrom': '',
                'yearTo': '',
                'months': '',
                'taxon': '',
                'reference': referenceValue,
                'referenceCategory': referenceCategory,
                'endemic': endemicValue,
                'conservationStatus': conservationStatusValue,
                'spatialFilter': spatialFilters.length === 0 ? '' : JSON.stringify(spatialFilters)
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
                && !parameters['conservationStatus']
                && !parameters['spatialFilter']
                && !parameters['boundary']) {
                Shared.Dispatcher.trigger('cluster:updateAdministrative', '');
                Shared.Router.clearSearch();
                return false
            }
            filterParameters = parameters;
            this.searchResultCollection.search(
                this.searchPanel,
                parameters,
                self.shouldUpdateUrl
            );

            if (!self.shouldUpdateUrl) {
                self.shouldUpdateUrl = true;
            }
        },
        searchClick: function () {
            // if (Shared.CurrentState.FETCH_CLUSTERS) {
            //     return true;
            // }
            Shared.Dispatcher.trigger('map:clearAllLayers');
            var searchValue = $('#search').val();
            this.search(searchValue);
        },
        searchEnter: function (e) {
            if (e.which === 13) {
                // if (Shared.CurrentState.FETCH_CLUSTERS) {
                //     return true;
                // }
                var searchValue = $('#search').val();
                this.search(searchValue);
            }
        },
        clearSearch: function () {
            Shared.CurrentState.SEARCH = false;
            Shared.Router.clearSearch();
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

            Shared.Dispatcher.trigger('map:resetSitesLayer');
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
            target.closest('.row').find('select').val('').trigger("chosen:updated");
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
        },
        handleClearConservationClicked: function (e) {
            this.clearSelectedConservationStatus();
            if (Shared.CurrentState.SEARCH) {
                this.searchClick();
            }
        },
        filtersUpdated: function (filters) {
            var self = this;
            var allFilters = {};

            var urlParams = new URLSearchParams(filters);
            for (var filter of urlParams.entries()) {
                if (filter[1]) {
                    allFilters[filter[0]] = filter[1];
                }
            }

            // Category
            if (allFilters.hasOwnProperty('category')) {
                var categories = JSON.parse(allFilters['category']);
                var originFilterWrapper = this.$el.find('#origin-filter-wrapper');
                $.each(categories, function (index, category) {
                    $('#' + category).prop('checked', true);
                });
                var buttons = originFilterWrapper.find('.origin-btn');
                $.each(buttons, function (index, button) {
                    var $button = $(button);
                    if ($.inArray($button.data('origin'), categories) > -1) {
                        $button.addClass('selected');
                    }
                })
            }

            // Collectors
            self.initialSelectedCollectors = [];
            if (allFilters.hasOwnProperty('collector')) {
                self.initialSelectedCollectors = JSON.parse(allFilters['collector']);
            }

            // Study referebce
            self.initialSelectedStudyReference = [];
            if (allFilters.hasOwnProperty('reference')) {
                self.initialSelectedStudyReference = JSON.parse(allFilters['reference']);
            }

            // Endemic
            self.initialSelectedEndemic = [];
            if (allFilters.hasOwnProperty('endemic')) {
                self.initialSelectedEndemic = JSON.parse(allFilters['endemic']);
                if (self.initialSelectedEndemic.length > 0) {
                    $('#native-origin-btn').addClass('selected');
                }
            }

            // Reference category
            self.initialSelectedReferenceCategory = [];
            if (allFilters.hasOwnProperty('referenceCategory')) {
                self.initialSelectedReferenceCategory = JSON.parse(allFilters['referenceCategory']);
            }

            // Date
            if (allFilters.hasOwnProperty('yearFrom')) {
                self.initialYearFrom = allFilters['yearFrom'];
            }
            if (allFilters.hasOwnProperty('yearTo')) {
                self.initialYearTo = allFilters['yearTo'];
            }

            if (this.initialYearFrom && this.initialYearTo) {
                $('#year-from').html(Math.floor(this.initialYearFrom));
                $('#year-to').html(Math.floor(this.initialYearTo));
                this.yearSlider.set([this.initialYearFrom, this.initialYearTo]);
            }

            // Months
            if (allFilters.hasOwnProperty('months')) {
                var months = allFilters['months'].split(',');
                $('#month-selector').find('input:checkbox').each(function () {
                    if ($.inArray($(this).val(), months) > -1) {
                        $(this).prop('checked', true);
                    }
                });
            }

            // Conservation status
            if (allFilters.hasOwnProperty('conservationStatus')) {
                var conservationStatus = JSON.parse(allFilters['conservationStatus']);
                $('#conservation-status').val(conservationStatus);
            }

            // River catchment
            if (allFilters.hasOwnProperty('spatialFilter')) {
                this.spatialFilterView.selectedSpatialFilters = JSON.parse(allFilters['spatialFilter']);
            }

            // Boundary
            if (allFilters.hasOwnProperty('boundary')) {
                this.spatialFilterView.selectedPoliticalRegions = JSON.parse(allFilters['boundary']);
            }
        },
        showMoreSites: function () {
            this.searchResultCollection.fetchMoreSites();
        }
    })

});
