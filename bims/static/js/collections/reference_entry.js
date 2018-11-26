define(['backbone', 'models/reference_entry'], function (Backbone, ReferenceEntry) {
   return Backbone.Collection.extend({
        model: ReferenceEntry,
        url: "/api/list-entry-reference/",
        next: null,
        previous: null,
        count: 0,
        parse: function (response) {
            if (response.hasOwnProperty('results')) {
                this.model = response['results'];
            }

            if (response.hasOwnProperty('next')) {
                this.next = response['next'];
            }

            if (response.hasOwnProperty('previous')) {
                this.previous = response['previous'];
            }

            if (response.hasOwnProperty('count')) {
                this.count = response['count'];
            }
        }
   })
});