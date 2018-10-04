define(['backbone', 'models/validate_data'], function (Backbone, ValidateData) {
   return Backbone.Collection.extend({
        model: ValidateData,
        apiUrl: "/api/get-unvalidated-records/",
        paginationData: null,
        updateUrl: function (page) {
            this.url = this.apiUrl + '?page=' + page
        },
        parse: function (response) {
            var result = response['data'];
            this.paginationData = response['pagination'];
            return result
        }
   })
});
