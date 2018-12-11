define([
    'jquery',
    'backbone',
    'models/search_result',
    'views/search_result',
    'shared'], function ($, Backbone, SearchModel, SearchResultView, Shared) {
    return Backbone.Collection.extend({
        model: SearchModel,
        url: "",
        searchUrl: "/api/search/",
        viewCollection: [],
        searchPanel: null,
        searchValue: '',
        status: '',
        isFuzzySearch: false,
        initialSearch: true,
        secondSearch: false,
        searchFinish: false,
        sitesData: [],
        recordsData: [],
        totalRecords: 0,
        totalSites: 0,
        modelId: function (attrs) {
            return attrs.record_type + "-" + attrs.id;
        },
        search: function (searchPanel, parameters) {
            var self = this;
            this.totalRecords = 0;
            this.totalSites = 0;
            this.searchValue = parameters['search'];
            this.collectorValue = parameters['collector'];
            this.categoryValue = parameters['category'];
            this.yearFrom = parameters['yearFrom'];
            this.yearTo = parameters['yearTo'];
            this.months = parameters['months'];
            this.boundary = parameters['boundary'];
            this.userBoundary = parameters['userBoundary'];
            this.referenceCategory = parameters['referenceCategory'];
            this.endemic = parameters['endemic'];
            this.reference = parameters['reference'];

            this.url = this.searchUrl +
                '?search=' + this.searchValue +
                '&collector=' + this.collectorValue +
                '&category=' + this.categoryValue +
                '&yearFrom=' + this.yearFrom +
                '&yearTo=' + this.yearTo +
                '&months=' + this.months +
                '&boundary=' + this.boundary +
                '&userBoundary=' + this.userBoundary +
                '&referenceCategory=' + this.referenceCategory +
                '&endemic=' + this.endemic +
                '&reference=' + this.reference;
            this.searchPanel = searchPanel;
            this.searchPanel.showSearchLoading();
            this.getSearchResults();
        },
        hideAll: function (e) {
            if ($(e.target).data('visibility')) {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-down');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-up');
                $(e.target).nextAll().hide();
                $(e.target).data('visibility', false)
            } else {
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-down');
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-up');
                $(e.target).nextAll().show();
                $(e.target).data('visibility', true)
            }
        },
        getSearchResults: function() {
            var self = this;
            return this.fetch({
                success: function () {
                    Shared.CurrentState.SEARCH = true;
                },
                complete: function () {
                    var timeout = 2000;
                    if (self.initialSearch) {
                        timeout = 500;
                        self.initialSearch = false;
                        self.secondSearch = true;
                    }
                    if (self.secondSearch) {
                        timeout = 1000;
                        self.secondSearch = true;
                    }
                    if(self.status === 'processing') {
                        setTimeout(function () {
                            self.getSearchResults()
                        }, timeout);
                    }
                }
            })
        },
        parse: function (response) {
            if (response.hasOwnProperty('records')) {
                this.recordsData = response['records'];
            }
            if (response.hasOwnProperty('sites')) {
                this.sitesData = response['sites'];
            }
            if (response.hasOwnProperty('fuzzy_search')) {
                this.isFuzzySearch = response['fuzzy_search'];
            }
            if (response.hasOwnProperty('status')) {
                this.status = response['status']['current_status'];
            }
            if (response.hasOwnProperty('total_records')) {
                this.totalRecords = response['total_records'];
            }
            if (response.hasOwnProperty('total_sites')) {
                this.totalSites = response['total_sites'];
            }
            this.renderCollection();
        },
        renderCollection: function () {
            var self = this;
            var searchResultTitle = this.searchValue;
            if (this.isFuzzySearch) {
                searchResultTitle = 'similar to ' + searchResultTitle;
            }
            this.searchPanel.updatesearchPanelTitle(searchResultTitle);
            if (this.models.length === 1) {
                if (this.models[0]['attributes'].hasOwnProperty('results')) {
                    self.searchPanel.fillPanelHtml(this.models[0]['attributes']['results']);
                    return false;
                }
            }

            var $searchResultsWrapper = $('<div></div>');
            $searchResultsWrapper.append(
                '<div class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> SITES ' +
                '(<span id="site-list-number"></span>) ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div>' +
                '<div id="site-list" class="search-results-section"></div>' +
                '</div>');
            $searchResultsWrapper.append(
                '<div class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="true"> TAXA ' +
                '(<span id="taxa-list-number"></span>) ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div>' +
                '<div id="taxa-list" class="search-results-section"></div>' +
                '</div>');

            self.searchPanel.fillPanelHtml($searchResultsWrapper);

            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];

            var recordsCount = this.totalRecords.toString();
            var siteCount = this.totalSites.toString();
            var speciesListName = [];

            if (self.status === 'finish') {
                $.each(this.recordsData, function (key, data) {
                    var searchModel = new SearchModel({
                        id: key,
                        count: data['c'],
                        name: data['n'],
                        highlight: data['h'],
                        record_type: 'taxa'
                    });
                    var searchResultView = new SearchResultView({
                        model: searchModel
                    });
                    self.viewCollection.push(searchResultView);
                    speciesListName.push(searchResultView.model.get('name'));
                });
                $.each(this.sitesData, function (key, data) {
                    var searchModel = new SearchModel({
                        id: key,
                        count: data['c'],
                        name: data['n'],
                        record_type: 'site'
                    });
                    var searchResultView = new SearchResultView({
                        model: searchModel
                    });
                    self.viewCollection.push(searchResultView);
                });
            }

            var taxaListNumberElm = $('#taxa-list-number');
            var siteListNumberElm = $('#site-list-number');

            $searchResultsWrapper.find('.search-results-total').click(self.hideAll);
            $searchResultsWrapper.find('.search-results-total').click();
            $searchResultsWrapper.find('.search-results-total').unbind();

            if (self.status === 'processing') {
                recordsCount += ' ...loading';
                siteCount += ' ...loading';
            } else if (self.status === 'finish') {
                $searchResultsWrapper.find('.search-results-total').click(self.hideAll);
            }
            taxaListNumberElm.html(recordsCount);
            siteListNumberElm.html(siteCount);
            Shared.Dispatcher.trigger('siteDetail:updateCurrentSpeciesSearchResult', speciesListName);
        }
    })
});
