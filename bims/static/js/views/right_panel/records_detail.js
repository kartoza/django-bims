define(['backbone', 'ol', 'shared', 'underscore'], function (Backbone, ol, Shared, _) {
    return Backbone.View.extend({
        taxonName: null,
        siteDetail: null,
        taxonId: null,
        apiParameters: _.template("?taxon=<%= taxon %>&search=<%= search %>&siteId=<%= siteId %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&yearFrom=<%= yearFrom %>&yearTo=<%= yearTo %>&months=<%= months %>&boundary=<%= boundary %>&userBoundary=<%= userBoundary %>" +
            "&referenceCategory=<%= referenceCategory %>&reference=<%= reference %>"),
        dataRepresentation: {
            'collection_date': 'Collection Date',
            'collector': 'Collector',
            'notes': 'Notes',
        },
        initialize: function () {
            Shared.Dispatcher.on('recordsDetail:show', this.show, this);
        },
        show: function (taxon_id, taxon_name, site_detail) {
            this.taxonName = taxon_name;
            this.taxonId = taxon_id;
            this.siteDetail = site_detail;
            if (typeof filterParameters !== 'undefined') {
                this.parameters = filterParameters;
                this.parameters['taxon'] = this.taxonId;
            }
            this.url = '/api/get-bio-records/' + this.apiParameters(this.parameters);
            this.showDetail();
        },
        renderDetail: function (data) {
            var template = _.template($("#records-list-detail").html());
            var recordsTemplate = $(template());
            $.each(this.dataRepresentation, function (key, value) {
                recordsTemplate.append('<div class="records-list">\n' +
                                          '<p class="group-title">'+value+'</p>\n' +
                                          '<a class="group-description">'+data[key]+'</a>\n' +
                                       '</div>')
            });
            return recordsTemplate;
        },
        showDetail: function () {
            var self = this;

            // Render basic information
            var $detailWrapper = $('<div></div>');
            $detailWrapper.append(
                '<div id="records-list" class="search-results-wrapper">' +
                '<div class="search-results-total" data-visibility="false"> <span class="records-list-total"></span> Records ' +
                '</div></div>');

            Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
            Shared.Dispatcher.trigger('sidePanel:fillSidePanelHtml', $detailWrapper);
            Shared.Dispatcher.trigger('sidePanel:updateSidePanelTitle', self.taxonName);

            Shared.Dispatcher.trigger('sidePanel:showReturnButton');
            Shared.Dispatcher.trigger('sidePanel:addEventToReturnButton', function () {
                filterParameters['taxon'] = '';
                Shared.Dispatcher.trigger('sidePanel:hideReturnButton');
                Shared.Dispatcher.trigger(
                    'taxonDetail:show', self.taxonId, self.taxonName, self.siteDetail);
            });

            $.get({
                url: this.url,
                dataType: 'json',
                success: function (data) {
                    $detailWrapper.find('.records-list-total').html(data.length);
                    for(var i=0; i<data.length; i++) {
                        $('#records-list').append(self.renderDetail(data[i]));
                    }
                }
            })
        }
    })
});