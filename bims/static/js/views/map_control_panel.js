define(['backbone', 'underscore'], function (Backbone, _) {
   return Backbone.View.extend({
       template: _.template($('#map-control-panel').html()),
       searchBox: null,
       events: {
           'click .search-control': 'searchClicked',
           'click .filter-control': 'filterClicked',
           'click .location-control': 'locationClicked',
           'click .map-search-close': 'searchCloseClicked',
       },
       initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
       },
       searchClicked: function (e) {
            // show search div
            this.searchBox.show();
       },
       searchCloseClicked: function (e) {
            this.searchBox.hide();
       },
       filterClicked: function (e) {
       },
       locationClicked: function (e) {
       },
       render: function () {
            this.$el.html(this.template());
            this.searchBox = this.$el.find('.map-search-box');
            this.searchBox.hide();
            return this;
       }
   })
});
