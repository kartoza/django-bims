define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            original_species_name: '',
            collector: '',
            collection_date: '',
            common_name: '',
            highlighted_common_name: ''
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});
