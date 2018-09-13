define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        siteDetail: null,
        gbifId: null,
        taxonId: null,
        taxonName: null,
        initialize: function () {
            Shared.Dispatcher.on('taxonDetail:show', this.show, this);
        },
        show: function (id, taxonName, siteDetail) {
            this.taxonId = id;
            this.taxonName = taxonName;
            this.url = '/api/taxon/' + id;
            this.showDetail(taxonName, siteDetail);
        },
        hideAll: function (e) {
            if ($(e.target).data('visibility')) {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-down');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-up');
                $(e.target).nextAll().hide();
                $(e.target).data('visibility', false)
            } else {
                $(e.target).find('.filter-icon-arrow').addClass('fa-angle-up');
                $(e.target).find('.filter-icon-arrow').removeClass('fa-angle-down');
                $(e.target).nextAll().show();
                $(e.target).data('visibility', true)
            }
        },
        renderDetail: function (data) {
            var template = _.template($('#species-template').html());
            return template(data);
        },
        showRecords: function (e) {
            e.preventDefault();
            Shared.Dispatcher.trigger('recordsDetail:show', e.data.taxonId, e.data.taxonName, e.data.siteDetail);
        },
        renderThirdPartyData: function (data) {
            var $thirdPartyData = $('<div>');

            var template = _.template($('#third-party-template').html());
            $thirdPartyData.append(template({
                taxon_gbif_id: this.gbifId
            }));

            var $wrapper = $thirdPartyData.find('.third-party-wrapper');
            var mediaFound = false;
            var $fetchingInfoDiv = $thirdPartyData.find('.third-party-fetching-info');

            $.get({
                url: 'https://api.gbif.org/v1/occurrence/search?taxonKey='+this.gbifId+'&limit=5',
                dataType: 'json',
                success: function (data) {
                    var results = data['results'];

                    var firstColumn = Math.ceil(results.length/2);
                    var secondColumn = Math.floor(results.length/2);

                    var $firstColumnDiv = $('<div class="column">');
                    var $secondColumnDiv = $('<div class="column">');

                    for (var i=0; i < firstColumn; i++) {
                        var result = results[i];
                        if(!result.hasOwnProperty('media')) {
                            continue;
                        }
                        if(result['media'].length === 0) {
                            continue;
                        }
                        var media = result['media'][0];
                        if(!media.hasOwnProperty('identifier')) {
                            continue;
                        }
                        mediaFound = true;
                        if(mediaFound) {
                            $fetchingInfoDiv.hide();
                        }
                        $firstColumnDiv.append('<a href="'+media['references']+'">' +
                            '<img alt="'+media['rightsHolder']+'" src="'+media['identifier']+'" width="100%"/></a>');
                    }
                    for (var j=firstColumn; j < firstColumn+secondColumn; j++) {
                        var resultSecond = results[j];
                        if(!resultSecond.hasOwnProperty('media')) {
                            continue;
                        }
                        if(resultSecond['media'].length === 0) {
                            continue;
                        }
                        var mediaSecond = resultSecond['media'][0];
                        if(!mediaSecond.hasOwnProperty('identifier')) {
                            continue;
                        }
                        mediaFound = true;
                        if(mediaFound) {
                            $fetchingInfoDiv.hide();
                        }
                        $secondColumnDiv.append('<a href="'+mediaSecond['references']+'">' +
                            '<img alt="'+media['rightsHolder']+'" src="'+mediaSecond['identifier']+'" width="100%"/></a>');
                    }
                    $wrapper.append($firstColumnDiv);
                    $wrapper.append($secondColumnDiv);

                    if(!mediaFound) {
                        $fetchingInfoDiv.html('Media not found');
                    }

                }
            });

            return $thirdPartyData;
        },
        showDetail: function (name, siteDetail) {
            var self = this;
            // Render basic information
            var $detailWrapper = $('<div></div>');
            $detailWrapper.append(
                '<div id="species-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> Species details ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $detailWrapper.append(
                '<div id="third-party" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> 3rd Party Data ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $detailWrapper);
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', name);

            self.siteDetail = siteDetail;
            if (siteDetail) {
                Shared.Dispatcher.trigger('sidePanel:showReturnButton');
                Shared.Dispatcher.trigger('sidePanel:addEventToReturnButton', function () {
                    Shared.Dispatcher.trigger('sidePanel:hideReturnButton');
                    Shared.Dispatcher.trigger(
                        'siteDetail:show', siteDetail.id, siteDetail.name);
                });
            }

            $detailWrapper.find('.search-results-total').click(self.hideAll);
            $detailWrapper.find('.search-results-total').click();

            // call detail
            if (Shared.TaxonDetailXHRRequest) {
                Shared.TaxonDetailXHRRequest.abort();
                Shared.TaxonDetailXHRRequest = null;
            }
            Shared.TaxonDetailXHRRequest = $.get({
                url: this.url,
                dataType: 'json',
                success: function (data) {
                    self.gbifId = data['gbif_id'];
                    // render taxon detail
                    $('#species-detail').append(self.renderDetail(data));
                    $('#species-detail .iucn-status .name').css('background-color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('border-color', data.iucn_status_colour);
                    if (data.iucn_status_name == null) {
                        $('#species-detail .iucn-status').hide();
                    }

                    $('#third-party').click();
                    $('#third-party').append(self.renderThirdPartyData(data));

                    Shared.LocationSiteDetailXHRRequest = null;
                    $($('#species-detail').find('.records-link').get(0)).click({
                        taxonId: self.taxonId, taxonName: self.taxonName, siteDetail: self.siteDetail}, self.showRecords);
                },
                error: function (req, err) {

                }
            });
        }
    })
});
