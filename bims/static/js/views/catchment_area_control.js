define(['backbone', 'ol', 'shared'], function (Backbone, ol, Shared) {
    return Backbone.View.extend({
        catchmentAreaBoundaryUrl: "/api/boundary/geojson?ids=",
        initialize: function () {
            Shared.Dispatcher.on('catchmentArea:show-administrative', this.show, this);
            Shared.Dispatcher.on('catchmentArea:hide', this.hide, this);
        },
        hide: function () {
            Shared.Dispatcher.trigger('map:closeHighlightPinned');
        },
        show: function (ids) {
            if (this.catchmentAreaXHR) {
                this.catchmentAreaXHR.abort();
            }
            this.catchmentAreaXHR = $.get({
                url: this.catchmentAreaBoundaryUrl + ids,
                dataType: 'json',
                success: function (data) {
                    var features = data['features'];
                    if (features) {
                        $.each(features, function (index, feature) {
                            var olfeature = new ol.format.GeoJSON().readFeatures(feature, {
                                featureProjection: 'EPSG:3857'
                            });
                            if (index === 0) {
                                Shared.Dispatcher.trigger('map:switchHighlightPinned', olfeature, true);
                            } else {
                                Shared.Dispatcher.trigger('map:addHighlightPinnedFeature', olfeature[0]);
                            }
                        })
                    }
                },
                error: function () {
                }
            });
        }
    })
});
