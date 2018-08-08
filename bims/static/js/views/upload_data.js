define(['backbone', 'underscore', 'jquery', 'shared', 'ol'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        template: _.template($('#upload-data-modal').html()),
        uploadDataModal: null,
        $alertElement: null,
        $successAlertElement: null,
        $collectionDateElement: null,
        lon: null,
        lat: null,
        siteFeature: null,
        events: {
            'click .close': 'closeModal',
            'click .upload-data-button': 'uploadData'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.map = options.map;
        },
        render: function () {
            this.$el.html(this.template());
            this.uploadDataModal = this.$el.find('.modal');

            this.$alertElement = $(this.$el.find('.alert-danger')[0]);
            this.$alertElement.hide();

            this.$successAlertElement = $(this.$el.find('.alert-success')[0]);
            this.$successAlertElement.hide();

            // Collection Date Input
            this.$collectionDateElement = $(this.$el.find('#ud_collection_date')[0]);
            this.$collectionDateElement.datepicker();

            this.markerStyle = new ol.style.Style({
                image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        anchor: [0.5, 40],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        opacity: 0.75,
                        src: '/static/img/upload-marker-small.png'
                    })),
                });

            return this;
        },
        showModal: function (lon, lat, siteFeature) {
            this.lon = lon;
            this.lat = lat;
            this.siteFeature = siteFeature;

            var coordinates = ol.proj.fromLonLat([lon, lat]);
            this.markerPoint = new ol.Feature({
                geometry: new ol.geom.Point(coordinates)
            });

            this.map.getView().setCenter(coordinates);

            this.markerPoint.setStyle(this.markerStyle);

            this.vectorSource = new ol.source.Vector({
                features: [this.markerPoint]
            });

            this.vectorLayer = new ol.layer.Vector({
                source: this.vectorSource
            });

            this.map.addLayer(this.vectorLayer);

            if(this.siteFeature) {
                var site_coordinates =  ol.proj.transform(this.siteFeature.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326');
                this.lon = site_coordinates[0];
                this.lat = site_coordinates[1];
                var properties = this.siteFeature.getProperties();
                if(properties.hasOwnProperty('name'))
                    $('#ud_location_site').val(this.siteFeature.getProperties()['name']);
            }
            this.uploadDataModal.show();
        },
        closeModal: function () {
            this.lon = null;
            this.lat = null;
            this.map.removeLayer(this.vectorLayer);
            this.$alertElement.hide();
            this.$successAlertElement.hide();
            this.clearAllFields();
            this.uploadDataModal.hide();
        },
        clearAllFields: function () {
            var fields = this.$el.find(".ud-item");
            $.each(fields, function (i, field) {
                field.value = '';
            });
            if(this.siteFeature) {
                var properties = this.siteFeature.getProperties();
                if(properties.hasOwnProperty('name'))
                    $('#ud_location_site').val(this.siteFeature.getProperties()['name']);
            }
        },
        uploadData: function (e) {
            var self = this;
            var alertMessages = '';
            var uploadButton = $(e.target);
            self.$alertElement.hide();
            self.$successAlertElement.hide();

            // Check required Fields
            var requiredFields = this.$el.find(".ud-item-required");
            $.each(requiredFields, function(i, field) {
                if (!field.value)
                {
                    alertMessages += field.name + ' is required<br>';
                }
            });
            if(alertMessages.length > 0) {
                self.showErrorMessage(alertMessages);
                return false;
            }

            // Processing data
            var fields = this.$el.find(".ud-item");
            var dataToSend = {};
            $.each(fields, function (i, field) {
                dataToSend[field.id] = field.value;
            });

            dataToSend['csrfmiddlewaretoken'] = csrfmiddlewaretoken;
            dataToSend['lat'] = self.lat;
            dataToSend['lon'] = self.lon;

            uploadButton.html('Uploading...');
            uploadButton.prop('disabled', true);

            $.ajax({
                url: uploadDataUrl,
                method: "POST",
                dataType: 'json',
                data: dataToSend,
                success: function (response) {
                    if(response['status'] === 'success') {
                        self.showSuccessMessage(response['message']);
                    } else {
                        self.showErrorMessage(response['message'])
                    }
                },
                error: function (response) {
                    self.showErrorMessage(response)
                },
                complete: function () {
                    self.clearAllFields();
                    uploadButton.html('Upload');
                    uploadButton.prop('disabled', false);
                }
            });
        },
        showErrorMessage: function (message) {
            this.$alertElement.html(message);
            this.$alertElement.show();
            this.$successAlertElement.hide();
        },
        showSuccessMessage: function (message) {
            this.$successAlertElement.html(message);
            this.$successAlertElement.show();
            this.$alertElement.hide();
        }
    })
});