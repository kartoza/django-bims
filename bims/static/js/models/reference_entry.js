define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            title: '',
            type: ''
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});