define(['backbone', 'models/source_collection'], function (Backbone, SourceCollection) {
   return Backbone.Collection.extend({
       model: SourceCollection,
       url: listSourceCollectionAPIUrl
   })
});