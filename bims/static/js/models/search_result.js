define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            original_species_name: '',
            collector: '',
            collection_date: '',
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});
