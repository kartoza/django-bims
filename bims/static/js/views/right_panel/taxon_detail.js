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
            $thirdPartyData.append(template({}));

            var $wrapper = $thirdPartyData.find('.third-party-wrapper');
            var mediaFound = false;
            var $fetchingInfoDiv = $thirdPartyData.find('.third-party-fetching-info');

            $.get({
                url: 'https://api.gbif.org/v1/occurrence/search?taxonKey='+this.gbifId+'&limit=4',
                dataType: 'json',
                success: function (data) {
                    var results = data['results'];

                    var $rowWrapper = $('<div id="gbif-images-row" class="row"></div>');

                    var result = {};
                    for (let result_id in results)
                    {
                        var $firstColumnDiv = $('<div class="col-6" "></div>');
                        result = results[result_id];
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
                        $firstColumnDiv.append('<a target="_blank" href="'+media['references']+'">' +
                            '<img title="Source: '+media['publisher']+'" alt="'+media['rightsHolder']+'" src="'+media['identifier']+'" width="100%"/></a>');
                        $rowWrapper.append($firstColumnDiv);
                    }
                    $wrapper.append($rowWrapper);
                    if(!mediaFound) {
                        $fetchingInfoDiv.html('Media not found');
                    }
                }
            });

            return $thirdPartyData;
        },

        renderFBISBlocks: function(data, stretch_selection = false) {
            var $detailWrapper = $('<div class="container-fluid" style="padding-left: 0;"></div>');
            $detailWrapper.append(this.getHtmlForFBISBlocks(data, stretch_selection));
            return $detailWrapper;
        },


        getHtmlForFBISBlocks: function (new_data_in, stretch_selection) {
            var result_html = '<div class ="fbis-data-flex-block-row">'
            var data_in = new_data_in;
            var data_value = data_in.value;
            var data_title = data_in.value_title;
            var keys = data_in.keys;
            var key = '';
            var style_class = '';
            var for_count = 0;
            for (let key of keys) {
                for_count += 1;
                style_class = "fbis-rpanel-block";
                var temp_key = key;
                //Highlight my selected box with a different colour
                if (key === data_value || (!data_value && key === 'Unknown')) {
                    style_class += " fbis-rpanel-block-selected";
                    if(key === data_value) {
                        temp_key = data_title;
                    }
                    if (stretch_selection == true)
                    {
                        style_class += " flex-base-auto";
                    }
                }
                result_html += (`<div class="${style_class}">
                                 <div class="fbis-rpanel-block-text">
                                 ${temp_key}</div></div>`)
                
            };
            result_html += '</div>';
            return result_html;
        },

        showDetail: function (name, siteDetail, count) {
            var self = this;
            // Render basic information
            var $detailWrapper = $('<div></div>');
            $detailWrapper.append(
                '<div id="species-detail" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> Species details ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            var $overviewPanelTitle = $('<div><img src="/static/img/fish-2-grey.png" style="width:36px;">&nbsp;Overview</div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $detailWrapper);
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', $overviewPanelTitle);

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
            var request_data = '';
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

                    //iucn data
                    $('#species-detail .iucn-status .name').css('background-color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('border-color', data.iucn_status_colour);
                    if (data.iucn_status_name == null) {
                        $('#species-detail .iucn-status').hide();
                    }

                    //Header Table

                    $('#third-party-images').click();
                    $('#third-party-images').append(self.renderThirdPartyData(data));

                    speciesDetailContainer.find('#open-detailed-view').click(function () {
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

                    this.OriginInfoList = $('.origin-info-list-detail');
                    this.endemicInfoList= $('.endemic-info-list-detail');
                    this.conservationStatusList = $('.conservation-status-list-detail');

                    // Set origin
                    var origin_block_data = {};
                    origin_block_data['value'] = data['origin'];
                    origin_block_data['keys'] = ['Native', 'Non-Native'];
                    origin_block_data['value_title'] = data['origin'];
                    this.OriginInfoList.append(self.renderFBISBlocks(origin_block_data));

                    // Set endemic
                    var endemism_block_data = {};
                    endemism_block_data['value'] = data['endemism'];;
                    endemism_block_data['keys'] = Shared.EndemismList;
                    endemism_block_data['value_title'] = data['endemism'];
                    this.endemicInfoList.append(self.renderFBISBlocks(endemism_block_data));

                    //Set conservation status
                    var cons_status_block_data = {};
                    cons_status_block_data['value'] = data['iucn_status_name'];;
                    cons_status_block_data['keys'] = ['NE', 'DD', 'LC' ,'NT', 'VU', 'EN', 'CR', 'EW', 'EX'];
                    cons_status_block_data['value_title'] = data['iucn_status_name'] + ' (' + data['iucn_status_full_name'] + ')';
                    this.conservationStatusList.append(self.renderFBISBlocks(cons_status_block_data, true));

                },
                error: function (req, err) {

                }
            });
        },
    })
});


