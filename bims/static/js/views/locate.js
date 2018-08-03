define(['backbone', 'underscore', 'jquery', 'shared', 'ol'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        template: _.template($('#locate-coordinate-modal').html()),
        locateCoordinateModal: null,
        events: {
            'click .close': 'closeModal',
            'click #go-button': 'search',
        },
        formList: ['.coordinate-form', '.farm-form'],
        activeForm: null,
        render: function () {
            this.$el.html(this.template());
            this.locateCoordinateModal = this.$el.find('.modal');
            return this;
        },
        showModal: function (activeForm) {
            this.locateCoordinateModal.show();
             $.each(this.formList, function (key, formClass) {
                 $(formClass).hide();
             });
            $(activeForm).show();
            this.activeForm = activeForm;
        },
        closeModal: function () {
            this.locateCoordinateModal.hide();
        },
        search: function(e){
          if(this.activeForm === '.coordinate-form'){
              this.searchCoordinate(e)
          }else {
              var farmID = $('#farm-id').val();
              console.log('Search by Farm ID: ' + farmID);
          }
        },
        searchCoordinate: function (e) {
            var longitude = parseFloat($('#longitude').val());
            var latitude = parseFloat($('#latitude').val());
            var coordinates = [longitude, latitude];
            coordinates = ol.proj.transform(
                coordinates, ol.proj.get("EPSG:4326"), ol.proj.get("EPSG:3857"));
            Shared.Dispatcher.trigger('map:zoomToCoordinates', coordinates, 17);
            this.closeModal();
        },

    })
});