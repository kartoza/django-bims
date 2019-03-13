define([
    'jquery',
    'backbone',
    'models/search_result',
    'views/search_result',
    'shared'], function ($, Backbone, SearchModel, SearchResultView, Shared) {
    return Backbone.Collection.extend({
        model: SearchModel,
        url: "",
        searchUrl: "/api/search-v2/",
        siteResultUrl: "/api/site-search-result/",
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
        totalTaxa: 0,
        processID: 0,
        pageMoreSites: 2,
        modelId: function (attrs) {
            return attrs.record_type + "-" + attrs.id;
        },
        search: function (searchPanel, parameters, shouldUpdateUrl) {
            var self = this;
            this.totalRecords = 0;
            this.totalSites = 0;
            this.totalTaxa = 0;
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
            this.conservationStatus = parameters['conservationStatus'];
            this.riverCatchment = parameters['spatialFilter'];
            parameters['taxon'] = '';
            parameters['siteId'] = '';

            var templateUrl = _.template(Shared.SearchURLParametersTemplate);
            this.filters = templateUrl(parameters);
            this.url = this.searchUrl + this.filters;

            // Update permalink
            if (shouldUpdateUrl) {
                var linkUrl = 'search/';
                linkUrl += this.searchValue;
                linkUrl += '/' + this.filters.substring(1, this.filters.length);
                Shared.Router.updateUrl(linkUrl);
            }

            this.searchPanel = searchPanel;
            this.searchPanel.showSearchLoading();
            this.getSearchResults();
        },
        hideAll: function (e) {
            let $target = $(e.target);
            if (!$target.hasClass('search-results-total')) {
                $target = $target.parent();
            }
            if ($target.data('visibility')) {
                $target.find('.filter-icon-arrow').addClass('fa-angle-down');
                $target.find('.filter-icon-arrow').removeClass('fa-angle-up');
                $target.nextAll().hide();
                $target.data('visibility', false)
            } else {
                $target.find('.filter-icon-arrow').removeClass('fa-angle-down');
                $target.find('.filter-icon-arrow').addClass('fa-angle-up');
                $target.nextAll().show();
                $target.data('visibility', true)
            }
        },
        getSearchResults: function () {
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
                    if (self.status === 'processing') {
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
                this.status = response['status'];
            }
            if (response.hasOwnProperty('total_records')) {
                this.totalRecords = response['total_records'];
            }
            if (response.hasOwnProperty('total_sites')) {
                this.totalSites = response['total_sites'];
            }
            if (response.hasOwnProperty('total_unique_taxa')) {
                this.totalTaxa = response['total_unique_taxa'];
            }
            if (response.hasOwnProperty('sites_raw_query')) {
                this.sitesRawQuery = response['sites_raw_query'];
            }
            if (response.hasOwnProperty('process_id')) {
                this.processID = response['process_id'];
            }
            this.renderCollection();
        },
        renderCollection: function () {
            var self = this;
            var searchResultTitleDiv = $('<div>');
            searchResultTitleDiv.addClass('search-result-title-panel');
            searchResultTitleDiv.html(this.searchValue);
            if (this.isFuzzySearch) {
                searchResultTitleDiv.html('similar to ' + this.searchValue)
            }

            let totalSearchResults = $('<div>');
            totalSearchResults.addClass('total-search-results');
            totalSearchResults.html(this.totalRecords.toString() + ' records');

            var searchResultHeader = $('<div>');
            searchResultHeader.append(searchResultTitleDiv);
            searchResultHeader.append(totalSearchResults);

            this.searchPanel.updatesearchPanelTitle(searchResultHeader);
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
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i> <span class="site-detail-dashboard-button-wrapper"></span></div>' +
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
            var taxaCount = this.totalTaxa.toString();
            var speciesListName = [];

            if (self.status === 'finished') {
                Shared.Dispatcher.trigger('map:updateBiodiversityLayerParams', this.sitesRawQuery);
                $.each(this.recordsData, function (key, data) {
                    var searchModel = new SearchModel({
                        id: data['taxon_id'],
                        count: data['total'],
                        name: data['name'],
                        highlight: data['name'],
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
                        id: data['site_id'],
                        count: data['total'],
                        name: data['name'],
                        record_type: 'site'
                    });
                    var searchResultView = new SearchResultView({
                        model: searchModel
                    });
                    self.viewCollection.push(searchResultView);
                });

                // Set multiple site dashboard url
                var currentParameters = $.extend({}, filterParameters);
                var templateParameter = _.template(Shared.SearchURLParametersTemplate);
                var apiUrl = templateParameter(currentParameters);
                apiUrl = apiUrl.substr(1);
                var multipleSiteDashboardUrl = '/map/#site-detail/' + apiUrl;
                $searchResultsWrapper.find('.site-detail-dashboard-button-wrapper').append("<a href='" + multipleSiteDashboardUrl + "' class='badge badge-primary'>Show in dashboard</a>");
            }

            var taxaListNumberElm = $('#taxa-list-number');
            var siteListNumberElm = $('#site-list-number');

            $searchResultsWrapper.find('.search-results-total').click(self.hideAll);
            $searchResultsWrapper.find('.search-results-total').click();
            $searchResultsWrapper.find('.search-results-total').unbind();

            if (self.status === 'processing') {
                taxaCount += ' ...loading';
                siteCount += ' ...loading';
            } else if (self.status === 'finished') {
                $searchResultsWrapper.find('.search-results-total').click(self.hideAll);
            }
            taxaListNumberElm.html(taxaCount);
            siteListNumberElm.html(siteCount);
            if (self.sitesData.length < self.totalSites) {
                var searchModel = new SearchModel({
                    name: 'Show More',
                    record_type: 'show-more-site'
                });
                var searchResultView = new SearchResultView({
                    model: searchModel
                });
                self.viewCollection.push(searchResultView);
            }
            Shared.Dispatcher.trigger('siteDetail:updateCurrentSpeciesSearchResult', speciesListName);
        },
        fetchMoreSites: function (page) {
            var self = this;
            var siteResultUrl = this.siteResultUrl + '?process_id=' + this.processID + '&page=' + this.pageMoreSites;
            $.ajax({
                url: siteResultUrl,
                success: function (data) {
                    var siteData = data['data'];
                    for(var i=0; i<siteData.length; i++){
                        var searchModel = new SearchModel({
                            id: siteData[i]['site_id'],
                            count: siteData[i]['total'],
                            name: siteData[i]['name'],
                            record_type: 'site'
                        });
                        var searchResultView = new SearchResultView({
                            model: searchModel
                        });
                        self.viewCollection.push(searchResultView);
                    }
                    if(data['has_next']){
                        self.pageMoreSites += 1;
                        self.fetchMoreSites()
                    }else {
                        self.pageMoreSites = 2
                    }
                }
            })
        }
    })
});
