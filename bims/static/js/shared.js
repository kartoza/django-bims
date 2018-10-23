/*global define*/
'use strict';

define(['backbone', 'underscore', 'utils/storage'], function (Backbone, _, StorageUtil) {
    return {
        LocationSiteDetailXHRRequest: null,
        TaxonDetailXHRRequest: null,
        Dispatcher: _.extend({}, Backbone.Events),
        Router: {},
        ClusterSize: 30,
        StorageUtil: new StorageUtil(),
        UserBoundaries: {},
        UserBoundarySelected: [],
        AdminAreaSelected: [],
        SearchMode: false,
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
