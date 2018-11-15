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
        alertDiv: null,
        render: function () {
            this.$el.html(this.template());
            this.locateCoordinateModal = this.$el.find('.modal');
            this.alertDiv = this.$el.find('.alert');
            this.farmInput = this.$el.find('#farm-id');
            this.goButton = this.$el.find('#go-button');
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
                this.$el.find('.modal-title').html('Locate by Farm Portion Code');
                this.farmInput.autocomplete({
                    source: filterFarmIDUrl,
                    minLength: 3
                });
                this.farmInput.autocomplete( "option", "appendTo", "#locate-form" );
            } else {
                this.$el.find('.modal-title').html('Locate by Coordinate');
            }
        },
        closeModal: function () {
            this.alertDiv.hide();
            this.locateCoordinateModal.hide();
        },
        search: function(e){
            this.goButton.html('Fetching...');
            this.goButton.prop('disabled', true);
            if(this.activeForm === '.coordinate-form'){
                this.searchCoordinate(e)
            }else {
                var farmID = this.farmInput.val();
                this.searchFarmID(farmID);
            }
        },
        searchCoordinate: function (e) {
            var longitude = parseFloat($('#longitude').val());
            var latitude = parseFloat($('#latitude').val());
            if(isNaN(longitude) || isNaN(latitude)){
                this.alertDiv.html('Lat/Long is not a number');
                this.alertDiv.show();
                return false;
            }
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
                    self.goButton.html('GO');
                    self.goButton.prop('disabled', false);
                    // We need to rearrange the order since it has different
                    // format
                    if (Object.keys(data).length === 0 || !data) {
                        self.alertDiv.show();
                        self.alertDiv.html('Not able to zoom to farm ID: ' + farmID + ' because of empty data');
                    }
                    var envelope_extent = [
                        data['envelope_extent'][0],
                        data['envelope_extent'][1],
                        data['envelope_extent'][2],
                        data['envelope_extent'][3],
                    ];
                    Shared.Dispatcher.trigger(
                        'map:zoomToExtent', envelope_extent);
                    self.closeModal();
                },
                error: function (req, err) {
                    self.goButton.html('GO');
                    self.goButton.prop('disabled', false);
                    self.alertDiv.show();
                    self.alertDiv.html('Not able to zoom to farm ID: ' + farmID + ' because of ' + err);
                    alert('Not able to zoom to farm ID: ' + farmID + ' because of ' + err);
                }
            });
        }

    })
});