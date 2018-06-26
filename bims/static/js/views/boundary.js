define(['backbone', 'underscore', 'jquery', 'shared', 'ol'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        administrativeXhr: null,
        cache: {},
        renderAdministrativeBoundary: function (administrative, bbox) {
            var self = this;
            if (this.administrativeXhr) {
                this.administrativeXhr.abort();
            }
            if (administrative == 'country') {
                return
            }
            if (this.cache[administrative]) {
                Shared.Dispatcher.trigger('map:updateAdministrativeBoundary', this.cache[administrative])
            } else {
                this.administrativeXhr = $.ajax({
                    url: '/media/geojson/' + administrative + '.geojson/',
                    dataType: "json",
                    success: function (data) {
                        var features = (new ol.format.GeoJSON()).readFeatures(data, {
                            dataProjection: 'EPSG:4326',
                            featureProjection: 'EPSG:3857'
                        });
                        self.cache[administrative] = features;
                        Shared.Dispatcher.trigger('map:updateAdministrativeBoundary', features)
                    }
                });
            }
        }
    })
});
