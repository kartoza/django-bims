define(['backbone', 'underscore', 'jquery', 'shared', 'ol'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        template: _.template($('#locate-coordinate-modal').html()),
        locateCoordinateModal: null,
        events: {
            'click .close': 'closeModal',
            'click #go-button': 'search',
            'keyup #farm-id': 'filterFarmIDs'
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
        searchFarmID: function (e) {
            var farmID = $('#farm-id').val();
            // Get bounding box for farmID
            // Zoom to farmID

        },
        filterFarmIDs: function () {
            var self = this;
            var farmIDPattern = $('#farm-id').val();
            if (self.lastFarmIDFilter === farmIDPattern){
                return
            }
            self.lastFarmIDFilter = farmIDPattern;

            $( "#farm-id" ).autocomplete({minLength: 3,});



            if (farmIDPattern.length < 4){
                return
            }

            if (this.filterFarmIDXhr) {
                this.filterFarmIDXhr.abort();
            }

            var url = filterFarmIDUrl.replace('123456789', farmIDPattern);
            console.log(url);

            this.filterFarmIDXhr = $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    var farm_ids = data['farm_ids'];
                    console.log('Success search for [' + farmIDPattern + ']');
                    console.log('Number of match: ' + farm_ids.length);
                    console.log(farm_ids);
                    // $.each(farm_ids, function (index, farm_id) {
                    //     console.log(farm_id);
                    // });

                    self.farm_ids = farm_ids;
                    // $( "#farm-id" ).autocomplete({
                    //     source: farm_ids,
                    //     minLength: 3
                    // });
                    $( "#farm-id" ).autocomplete('option', 'source', farm_ids);
                    console.log('Show auto complete for [' + farmIDPattern + ']');

                },
                error: function (req, err) {
                    console.log(err);
                }
            });

        }

    })
});