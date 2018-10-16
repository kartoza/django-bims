define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            name: '',
            highlight: ''
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});
