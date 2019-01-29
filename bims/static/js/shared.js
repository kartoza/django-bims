/*global define*/
'use strict';

define(['backbone', 'underscore', 'utils/storage'], function (Backbone, _, StorageUtil) {
    return {
        SearchURLParametersTemplate: "?taxon=<%= taxon %>&search=<%= search %>&siteId=<%= siteId %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&yearFrom=<%= yearFrom %>&yearTo=<%= yearTo %>&months=<%= months %>" +
            "&boundary=<%= boundary %>&userBoundary=<%= userBoundary %>" +
            "&referenceCategory=<%= referenceCategory %>" +
            "&riverCatchment=<%= riverCatchment %>" +
            "&reference=<%= reference %>&endemic=<%= endemic %>&conservationStatus=<%= conservationStatus %>",
        LocationSiteDetailXHRRequest: null,
        TaxonDetailXHRRequest: null,
        GetFeatureXHRRequest: [],
        Dispatcher: _.extend({}, Backbone.Events),
        Router: {},
        ClusterSize: 30,
        StorageUtil: new StorageUtil(),
        UserBoundaries: {},
        UserBoundarySelected: [],
        PoliticalRegionBoundaries: null,
        AdminAreaSelected: [],
        LegendsDisplayed: false,
        GetFeatureRequested: false,
        CurrentState: {
            FETCH_CLUSTERS: false,
            SEARCH: false,
        },
        EVENTS: {
            SEARCH: {
                HIT: 'search:hit'
            },
            CLUSTER: {
                GET: 'clusterBiological:getClusters'
            }
        }
    };
});
