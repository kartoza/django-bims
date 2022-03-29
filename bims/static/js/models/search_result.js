define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            name: '',
            highlight: '',
            count: 0,
            survey: 0,
            record_type: '',
            total_thermal: 0
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});
