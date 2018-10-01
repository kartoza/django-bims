define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        category: function () {
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});