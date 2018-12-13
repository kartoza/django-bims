define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        siteDetail: null,
        gbifId: null,
        taxonId: null,
        taxonName: null,
        count: 0,
        initialize: function () {
            Shared.Dispatcher.on('taxonDetail:show', this.show, this);
        },
        show: function (id, taxonName, siteDetail, count) {
            this.taxonId = id;
            this.taxonName = taxonName;
            this.url = '/api/taxon/' + id;
            if (count) {
                this.count = count;
            }
            this.showDetail(taxonName, siteDetail, count);
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
        renderResources: function (data) {
            if(!data.hasOwnProperty('documents')) {
                return '';
            }
            var container = $('<div class="document-container"></div>');
            $.each(data['documents'], function (key, value) {
                var div = $('<div class="document-row"></div>');
                div.append('<img src="'+value['thumbnail_url']+'" height="25px">&nbsp;<a href="'+value['doc_file']+'" download>'+value['title']+'</a>');
                container.append(div);
            });
            return container;
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
        showDetail: function (name, siteDetail, count) {
            var self = this;
            // Render basic information
            var $detailWrapper = $('<div></div>');
            $detailWrapper.append(
                '<div id="species-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> Species details ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');
            $detailWrapper.append(
                '<div id="taxon-resources" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> Resources ' +
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
                    self.gbifId = data['gbif_key'];
                    if(self.count > 0) {
                        data['count'] = self.count;
                    }
                    var speciesDetailContainer = $('#species-detail');
                    // render taxon detail
                    speciesDetailContainer.append(self.renderDetail(data));
                    $('#species-detail .iucn-status .name').css('background-color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('border-color', data.iucn_status_colour);
                    if (data.iucn_status_name == null) {
                        $('#species-detail .iucn-status').hide();
                    }

                    $('#third-party').click();
                    $('#third-party').append(self.renderThirdPartyData(data));

                    var taxonomySystem = speciesDetailContainer.find('.taxonomy-system');

                    if(data.hasOwnProperty('kingdom')) {
                        taxonomySystem.append(
                            '' + data['kingdom'] + '<br>' +
                            '<i class="fa fa-arrow-down"></i><br>'
                        )
                    }
                    if(data.hasOwnProperty('phylum')) {
                        taxonomySystem.append(
                            '' + data['phylum'] + '<br>' +
                            '<i class="fa fa-arrow-down"></i><br>'
                        )
                    }
                    if(data.hasOwnProperty('class')) {
                        taxonomySystem.append(
                            '' + data['class'] + '<br>' +
                            '<i class="fa fa-arrow-down"></i><br>'
                        )
                    }
                    if(data.hasOwnProperty('order')) {
                        taxonomySystem.append(
                            '' + data['order'] + '<br>' +
                            '<i class="fa fa-arrow-down"></i><br>'
                        )
                    }
                    if(data.hasOwnProperty('family')) {
                        taxonomySystem.append(
                            '' + data['family'] + '<br>' +
                            '<i class="fa fa-arrow-down"></i><br>'
                        )
                    }
                    if(data.hasOwnProperty('genus')) {
                        taxonomySystem.append(
                            '' + data['genus'] + '<br>' +
                            '<i class="fa fa-arrow-down"></i><br>'
                        )
                    }
                    if(data.hasOwnProperty('species')) {
                        taxonomySystem.append(
                            '' + data['species'] + '<br>'
                        )
                    }

                    speciesDetailContainer.find('.open-detailed-view').click(function () {
                        Shared.Dispatcher.trigger('map:showTaxonDetailedDashboard', {
                            taxonId: self.taxonId,
                            taxonName: self.taxonName,
                            siteDetail: self.siteDetail
                        });
                    });

                    Shared.LocationSiteDetailXHRRequest = null;
                    $(speciesDetailContainer.find('.records-link').get(0)).click({
                        taxonId: self.taxonId, taxonName: self.taxonName, siteDetail: self.siteDetail}, self.showRecords);

                    var resourcesContainer = $('#taxon-resources');
                    resourcesContainer.append(self.renderResources(data));
                },
                error: function (req, err) {

                }
            });
        }
    })
});
