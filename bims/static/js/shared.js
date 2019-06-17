/*global define*/
'use strict';

define(['backbone', 'underscore', 'utils/storage', 'utils/color'], function (Backbone, _, StorageUtil, ColorUtil) {
    return {
        SearchURLParametersTemplate: "?taxon=<%= taxon %>&search=<%= search %>&siteId=<%= siteId %>" +
            "&collector=<%= collector %>&category=<%= category %>" +
            "&yearFrom=<%= yearFrom %>&yearTo=<%= yearTo %>&months=<%= months %>" +
            "&boundary=<%= boundary %>&userBoundary=<%= userBoundary %>" +
            "&referenceCategory=<%= referenceCategory %>" +
            "&spatialFilter=<%= spatialFilter %>" +
            "&reference=<%= reference %>&endemic=<%= endemic %>&conservationStatus=<%= conservationStatus %>" +
            "&modules=<%= modules %>&validated=<%= validated %>&sourceCollection=<%= sourceCollection %>" +
            "&ecologicalCategory=<%= ecologicalCategory %>",
        LocationSiteDetailXHRRequest: null,
        MultiSitesOverviewXHRRequest: null,
        TaxonDetailXHRRequest: null,
        GetFeatureXHRRequest: [],
        Dispatcher: _.extend({}, Backbone.Events),
        Router: {},
        ClusterSize: 30,
        FishModuleID: null,
        StorageUtil: new StorageUtil(),
        ColorUtil: new ColorUtil(),
        UserBoundaries: {},
        UserBoundarySelected: [],
        PoliticalRegionBoundaries: null,
        AdminAreaSelected: [],
        LegendsDisplayed: false,
        GetFeatureRequested: false,
        EndemismList: [],
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
