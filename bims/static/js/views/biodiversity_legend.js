define([
    'backbone',
    'underscore',
    'shared',
    'jquery'
    ], function (
        Backbone,
        _,
        Shared,
        $
        ) {
   return Backbone.View.extend({
       template: _.template($('#biodiversity-legend').html()),
       moved: false,
       render: function () {
            this.$el.html(this.template());
            this.container = $(this.$el.find('.bio-legend-wrapper').get(0));
            var biodiversitySelected = Shared.StorageUtil.getItemDict('Biodiversity', 'selected');
            if (biodiversitySelected !== null && biodiversitySelected === false) {
                this.hide();
            }
            return this;
        },
       initialize: function () {
            Shared.Dispatcher.on('biodiversityLegend:moveLeft', this.moveLeft, this);
            Shared.Dispatcher.on('biodiversityLegend:moveRight', this.moveRight, this);
            Shared.Dispatcher.on('biodiversityLegend:toggle', this.toggle, this);
            Shared.Dispatcher.on('biodiversityLegend:hide', this.hide, this);
            Shared.Dispatcher.on('biodiversityLegend:show', this.show, this);
       },
       moveLeft: function () {
           var self = this;
           if (this.moved) {
               return;
           }
           var panelWrapper = $('.panel-wrapper');
           var width = panelWrapper.width() + 5;
           self.moved = true;
           this.container.animate({
               "right": "+=" + width + 'px'
           }, 100, function () {
               // Animation complete
           })
       },
       moveRight: function () {
           var self = this;
           if (!self.moved) {
               return;
           }
           var panelWrapper = $('.panel-wrapper');
           var width = panelWrapper.width() + 5;
           self.moved = false;
           this.container.animate({
               "right": "-=" + width + "px"
           }, 100, function () {
               // Animation complete
           })
       },
       toggle: function () {
           this.container.toggle();
       },
       hide: function () {
           this.container.hide();
       },
       show: function () {
           this.container.show();
       }
   })
});