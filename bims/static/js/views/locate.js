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
        filterFarmIDXhr: null,
        farm_ids: [],
        lastFarmIDFilter: '',
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

            // Activate autocomplete for search by farm ID
            if (this.activeForm === '.farm-form'){
                $('#farm-id').autocomplete({
                    source: filterFarmIDUrl,
                    minLength: 3
                });
                $("#farm-id").autocomplete( "option", "appendTo", "#locate-form" );
            }
        },
        closeModal: function () {
            this.locateCoordinateModal.hide();
        },
        search: function(e){
          if(this.activeForm === '.coordinate-form'){
              this.searchCoordinate(e)
          }else {
              var farmID = $('#farm-id').val();
              this.searchFarmID(farmID);
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
        searchFarmID: function (farmID) {
            var self = this;
            if (self.locateFarmXhr) {
                self.locateFarmXhr.abort();
            }

            var url = getFarmUrl.replace('123456789', farmID);

            self.locateFarmXhr = $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    // We need to rearrange the order since it has different
                    // format
                    var envelope_extent = [
                        data['envelope_extent'][1],
                        data['envelope_extent'][0],
                        data['envelope_extent'][3],
                        data['envelope_extent'][2],
                    ];
                    Shared.Dispatcher.trigger(
                        'map:zoomToExtent', envelope_extent);
                    self.closeModal();
                },
                error: function (req, err) {
                    console.log(err);
                    alert('Not able to zoom to farm ID: ' + farmID + ' because of ' + err);
                }
            });
        }

    })
});