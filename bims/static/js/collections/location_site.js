define(['backbone', 'models/location_site'], function (Backbone, LocationSite) {
   return Backbone.Collection.extend({
       model: LocationSite,
       url: "/api/location-site/"
   })
});
