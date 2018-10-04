define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});