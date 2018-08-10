define(['backbone', 'models/biological'], function (Backbone, Biological) {
   return Backbone.Collection.extend({
       model: Biological,
       url: "/api/biological-collections/"
   })
});
