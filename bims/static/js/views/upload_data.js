define(['backbone', 'underscore', 'jquery', 'shared', 'ol', 'collections/reference_entry', 'chosen'], function (
    Backbone,
    _,
    $,
    Shared,
    ol,
    ReferenceEntry, Chosen) {
    return Backbone.View.extend({
        template: _.template($('#upload-data-modal').html()),
        uploadDataModal: null,
        $alertElement: null,
        $successAlertElement: null,
        $collectionDateElement: null,
        lon: null,
        lat: null,
        siteFeature: null,
        referenceEntryFetched: false,
        referenceEntries: [],
        events: {
            'click .close': 'closeModal',
            'click .upload-data-button': 'uploadData',
            'click #update_coordinate': 'updateCoordinate',
            'click .btn-ud-new-site': 'addNewSite'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.map = options.map;
            this.referenceEntryList = new ReferenceEntry();
            this.fetchReferenceList(1);
        },
        addNewSite: function (e) {
            var locationSiteInput = $('#ud_location_site');
            locationSiteInput.val('');
            locationSiteInput.focus();
            this.addNewSiteButton.hide();
            this.sameSiteInfo.hide();
        },
        fetchReferenceList: function (page) {
            var self = this;
            var url = '';
            if (page) {
                url = self.referenceEntryList.url + '?page=' + page;
            } else {
                url = self.referenceEntryList.url;
            }
            self.referenceEntryList.fetch({
                url: url,
                success: function (data) {
                    if (data.model.length > 0) {
                        for (var i=0; i < data.model.length; i++) {
                            self.referencesSelectDiv.append($('<option></option>')
                                .attr('value', data.model[i].id).text(data.model[i].title + ' [' + data.model[i].journal + ']'));
                            self.referencesSelectDiv.trigger("chosen:updated");
                        }
                        self.referenceEntries.push.apply(self.referenceEntries, data.model);
                    }
                    if (data.next) {
                        self.referenceEntryList.url = data.next;
                        self.fetchReferenceList();
                    } else {
                        self.referenceEntryFetched = true;
                    }
                }
            });
        },
        updateCoordinate: function (e) {
            e.preventDefault();
            var currentLat = parseFloat(this.latInput.val());
            var currentLon = parseFloat(this.lonInput.val());

            var coordinatesChanged = currentLat !== this.lat.toFixed(3) || currentLon !== this.lon.toFixed(3);

            if (coordinatesChanged) {
                this.lon = null;
                this.lat = null;
                this.map.removeLayer(this.vectorLayer);
                this.$alertElement.hide();
                this.$successAlertElement.hide();
                this.showModal(currentLon, currentLat, this.siteFeature);
            }
        },
        render: function () {
            this.$el.html(this.template());
            this.uploadDataModal = this.$el.find('.modal');

            this.latInput = this.$el.find('#current_lat');
            this.lonInput = this.$el.find('#current_lon');
            this.addNewSiteButton = this.$el.find('.btn-ud-new-site');
            this.addNewSiteButton.hide();

            this.sameSiteInfo = this.$el.find('.ud-badge-same-site');
            this.sameSiteInfo.hide();

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

            this.referencesSelectDiv = this.$el.find('#ud_references');
            this.referencesSelectDiv.chosen();
            return this;
        },
        showModal: function (lon, lat, siteFeature) {
            this.lon = lon;
            this.lat = lat;
            this.siteFeature = siteFeature;

            this.latInput.val(lat.toFixed(3));
            this.lonInput.val(lon.toFixed(3));

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
                if(properties.hasOwnProperty('name')) {
                    $('#ud_location_site').val(this.siteFeature.getProperties()['name']);
                    this.addNewSiteButton.show();
                }
            }
            this.uploadDataModal.show();
        },
        closeModal: function () {
            this.lon = null;
            this.lat = null;
            this.map.removeLayer(this.vectorLayer);
            this.$alertElement.hide();
            this.$successAlertElement.hide();
            this.clearAllFields([]);
            this.uploadDataModal.hide();
            this.sameSiteInfo.hide();
            this.addNewSiteButton.hide();
        },
        clearAllFields: function (exceptions) {
            var fields = this.$el.find(".ud-item");
            $.each(fields, function (i, field) {
                var id = field.getAttribute('id');
                if (exceptions) {
                    if (exceptions.indexOf(id) > -1) {
                        return;
                    }
                }
                field.value = '';
            });
            if(this.siteFeature && exceptions.indexOf('ud_location_site') === -1) {
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
                        self.addNewSiteButton.show();
                        self.sameSiteInfo.show();
                        self.clearAllFields(['ud_location_site']);
                    } else {
                        self.showErrorMessage(response['message']);
                        self.clearAllFields([]);
                    }
                },
                error: function (response) {
                    self.showErrorMessage(response)
                },
                complete: function () {
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