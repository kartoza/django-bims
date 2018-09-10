define([
    'backbone',
    'underscore',
    'shared'
    ], function (
        Backbone,
        _,
        Shared
        ) {
   return Backbone.View.extend({
       template: _.template($('#biodiversity-legend').html()),
       moved: false,
       render: function () {
            this.$el.html(this.template());
            this.container = $(this.$el.find('.bio-legend-wrapper').get(0));
            return this;
        },
       initialize: function () {
            Shared.Dispatcher.on('biodiversityLegend:moveLeft', this.moveLeft, this);
            Shared.Dispatcher.on('biodiversityLegend:moveRight', this.moveRight, this);
       },
       moveLeft: function () {
           var self = this;
           if (this.moved) {
               return;
           }
           this.container.animate({
               "right": "+=270px"
           }, 100, function () {
               // Animation complete
               self.moved = true;
           })
       },
       moveRight: function () {
           var self = this;
           if (!self.moved) {
               return;
           }
           this.container.animate({
               "right": "-=270px"
           }, 100, function () {
               // Animation complete
               self.moved = false;
           })
       },
       hide: function () {
           this.container.hide();
       },
       show: function () {
           this.container.show();
       }
   })
});