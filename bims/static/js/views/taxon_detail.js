define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        id: 0,
        siteDetail: null,
        initialize: function () {
            Shared.Dispatcher.on('taxonDetail:show', this.show, this);
        },
        show: function (id, taxonName, siteDetail) {
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
                '<div class="search-results-total" data-visibility="true"> 3rd Party Data ' +
                '<i class="fa fa-angle-down pull-right filter-icon-arrow"></i></div></div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $detailWrapper);
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', name);

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
                    // render taxon detail
                    $('#species-detail').append(self.renderDetail(data));
                    $('#species-detail .iucn-status .name').css('background-color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('color', data.iucn_status_colour);
                    $('#species-detail .iucn-status .full-name').css('border-color', data.iucn_status_colour);
                    if (data.iucn_status_name == null) {
                        $('#species-detail .iucn-status').hide();
                    }
                    Shared.LocationSiteDetailXHRRequest = null;
                },
                error: function (req, err) {

                }
            });
        }
    })
});
