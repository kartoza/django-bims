define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            name: '',
            highlight: '',
            count: 0,
            survey: 0,
            record_type: ''
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});
