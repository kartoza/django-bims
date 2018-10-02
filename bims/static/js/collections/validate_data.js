define(['backbone', 'models/validate_data'], function (Backbone, ValidateData) {
   return Backbone.Collection.extend({
        model: ValidateData,
        apiUrl: "/api/get-unvalidated-records/",
        updateUrl: function (page) {
            this.url = this.apiUrl + '?page=' + page
        },
   })
});
