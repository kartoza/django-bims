define(['backbone', 'models/reference_category'], function (Backbone, ReferenceCategory) {
   return Backbone.Collection.extend({
       model: ReferenceCategory,
       url: "/api/list-reference-category/"
   })
});