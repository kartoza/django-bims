define(['backbone', 'underscore'], function(Backbone, _) {

    var UtilClass = function() {
        this.initialize.apply(this, arguments);
    };

    //give Class events and a default constructor
    _.extend(UtilClass.prototype, Backbone.Events, {initialize: function() {}});

    //copy the extend feature from one of the backbone classes
    UtilClass.extend = Backbone.Model.extend;

    return UtilClass;
});
