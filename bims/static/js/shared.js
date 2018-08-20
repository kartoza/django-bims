/*global define*/
'use strict';

define(['backbone', 'underscore'], function (Backbone, _) {
    return {
        LocationSiteDetailXHRRequest: null,
        TaxonDetailXHRRequest: null,
        Dispatcher: _.extend({}, Backbone.Events),
        Router: {}
    };
});
