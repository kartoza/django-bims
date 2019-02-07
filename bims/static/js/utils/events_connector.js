define(['backbone', 'utils/class', 'shared'], function (Backbone, UtilClass, Shared) {
    var EventsConnector = UtilClass.extend({
        initialize: function () {
            Shared.Dispatcher.on(Shared.EVENTS.SEARCH.HIT, this.searchHit, this);
            Shared.Dispatcher.on('searchResult:taxonClicked', this.searchResultTaxonClicked, this);
            Shared.Dispatcher.on('searchResult:siteClicked', this.searchResultSiteClicked, this);
        },
        searchHit: function (parameters) {
            // TODO : Change this to geoserver cluster
            // Shared.Dispatcher.trigger(Shared.EVENTS.CLUSTER.GET, parameters);
        },
        searchResultTaxonClicked: function (taxon) {
            if (!taxon) {
                return false;
            }

            try {
                var taxonId = taxon['id'];
                var taxonName = taxon['name'];
                var taxonCount = taxon['count'];
            } catch (err) {
                console.log(err.message);
                return false;
            }

            filterParameters['siteId'] = '';

            Shared.Dispatcher.trigger('map:updateClusterBiologicalCollectionTaxon',
                taxonId,
                taxonName
            );
            Shared.Dispatcher.trigger('taxonDetail:show',
                taxonId,
                taxonName,
                null,
                taxonCount
            );
        },
        searchResultSiteClicked: function (site) {
            if(!site) {
                return false;
            }
            if(!site.hasOwnProperty('id') || !site.hasOwnProperty('name')) {
                return false;
            }

            Shared.Dispatcher.trigger('clusterBiological:clearFilterByTaxon');

            var zoomToObject = true;
            filterParameters['siteId'] = site['id'];
            Shared.Dispatcher.trigger('siteDetail:show',
                site['id'], site['name'], zoomToObject);
        }
    });
    return EventsConnector;
});
