define(['backbone', 'models/fish'], function (Backbone, Fish) {
   return Backbone.Collection.extend({
       model: Fish,
       url: "/api/fish-collections/"
   })
});
