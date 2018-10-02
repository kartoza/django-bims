define(['backbone', 'ol', 'shared', 'underscore', 'jquery'], function (Backbone, ol, Shared, _, $) {
    return Backbone.View.extend({
        template: _.template($('#validate-data-detail-container').html()),
        model: null,
        events: {
            'click .show-map-button': 'showOnMap'
        },
        initialize: function () {
        },
        showOnMap: function () {
            console.log(this.model);
        },
        render: function () {
            var name = this.model.get('original_species_name');
            var description = this.model.get('category');
            var data = {
                id: this.model.get('id'),
                name: name,
                description: description
            };
            this.$el.html(this.template(data));
            return this;
        }
    })
});
