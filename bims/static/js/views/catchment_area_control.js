define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        catchmentAreaListUrl: "/api/list-boundary/",
        initialize: function () {
            Shared.Dispatcher.on('catchmentArea:show', this.show, this);
        },
        show: function (id) {
            var self = this;
            if (this.catchmentAreaXHR) {
                this.catchmentAreaXHR.abort();
            }
            // this.catchmentAreaXHR = $.get({
            //     url: this.catchmentAreaUrl({
            //         'geocontextUrl': geocontextUrl,
            //         'latitude': latitude,
            //         'longitude': longitude,
            //         'catchment_area_key': key
            //     }),
            //     dataType: 'json',
            //     success: function (data) {
            //         $('#loading-warning').hide();
            //         var feature = data['features'][0];
            //         if (feature) {
            //             self.catchmentArea = feature['geometry']['coordinates'];
            //             var features = new ol.format.GeoJSON().readFeatures(data, {
            //                 featureProjection: 'EPSG:3857'
            //             });
            //             Shared.Dispatcher.trigger('search:searchCollection');
            //             Shared.Dispatcher.trigger('map:switchHighlight', features);
            //         }
            //     },
            //     error: function () {
            //         $('#loading-warning').hide();
            //         $('#fetching-error').show();
            //     }
            // });
        }
    })
});
