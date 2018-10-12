define(['backbone', 'ol', 'shared', 'jquery'], function (Backbone, ol, Shared, $) {
    return Backbone.View.extend({
        catchmentAreaBoundaryUrl: "/api/boundary/geojson?ids=",
        initialize: function () {
            Shared.Dispatcher.on('catchmentArea:show-administrative', this.show, this);
            Shared.Dispatcher.on('catchmentArea:hide', this.hide, this);
            Shared.Dispatcher.on('politicalRegion:clear', this.clear, this);
        },
        clear: function () {
            if (this.catchmentAreaXHR) {
                this.catchmentAreaXHR.abort();
            }
            $.each(Shared.AdminAreaSelected, function (index, id) {
                Shared.Dispatcher.trigger('map:removeHighlightPinnedFeature', id);
            });
            Shared.AdminAreaSelected = [];
        },
        hide: function () {
            Shared.Dispatcher.trigger('map:closeHighlightPinned');
            Shared.AdminAreaSelected = [];
        },
        show: function (ids) {
            if (this.catchmentAreaXHR) {
                this.catchmentAreaXHR.abort();
            }

            this.catchmentAreaXHR = $.get({
                url: this.catchmentAreaBoundaryUrl + ids,
                dataType: 'json',
                success: function (data) {
                    $.each(Shared.AdminAreaSelected, function (index, id) {
                        Shared.Dispatcher.trigger('map:removeHighlightPinnedFeature', id);
                    });

                    Shared.AdminAreaSelected = [];

                    var features = data['features'];
                    if (features) {
                        var isUserBoundaryDisplayed = Shared.UserBoundarySelected.length > 0;
                        $.each(features, function (index, feature) {
                            var olfeature = new ol.format.GeoJSON().readFeatures(feature, {
                                featureProjection: 'EPSG:3857'
                            });

                            for (var i=0;i<olfeature.length;i++) {
                                var id = 'adminArea-'+i+'-'+index;
                                olfeature[i].setProperties({'id': id});
                                Shared.AdminAreaSelected.push(id);
                            }

                            if (index === 0 && !isUserBoundaryDisplayed) {
                                Shared.Dispatcher.trigger('map:switchHighlightPinned', olfeature, true);
                            } else {
                                Shared.Dispatcher.trigger('map:addHighlightPinnedFeature', olfeature[0]);
                            }
                        });
                        Shared.Dispatcher.trigger('map:zoomToHighlightPinnedFeatures');
                    }
                },
                error: function () {
                    console.log('error');
                }
            });
        }
    })
});
