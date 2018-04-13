/*global define*/
'use strict';

define(['backbone', 'underscore'], function (Backbone, _) {
    return {
        Dispatcher: _.extend({}, Backbone.Events)
    };
});
