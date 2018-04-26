define(['backbone', 'underscore'], function (Backbone, _) {
   return Backbone.View.extend({
       template: _.template($('#map-control-panel').html()),
       events: {
           'click .search-control': 'searchClicked',
           'click .filter-control': 'filterClicked',
           'click .location-control': 'locationClicked',
       },
       initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.render();
       },
       searchClicked: function (e) {
       },
       filterClicked: function (e) {
       },
       locationClicked: function (e) {
       },
       render: function () {
           this.$el.html(this.template());
           return this;
       }
   })
});
