define(['backbone', 'ol', 'shared', 'jquery'], function (Backbone, ol, Shared, $) {
    return Backbone.View.extend({
        catchmentAreaBoundaryUrl: "/api/boundary/geojson?ids=",
        initialize: function () {
            Shared.Dispatcher.on('catchmentArea:show-administrative', this.show, this);
            Shared.Dispatcher.on('catchmentArea:hide', this.hide, this);
            Shared.Dispatcher.on('politicalRegion:clear', this.clear, this);
        },
        clear: function () {
            if (this.politicalRegionXHR) {
                this.politicalRegionXHR.abort();
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
        getNodesWithoutChildren: function (boundaries, idsArray, isRoot = false) {
            var nodeIds = [];
            var self = this;
            $.each(boundaries, function (index, boundary) {
                if (idsArray.includes(boundary['value'].toString())) {
                    if (boundary['children'].length > 0) {
                        nodeIds.push.apply(nodeIds, self.getNodesWithoutChildren(boundary['children'], idsArray));
                    }
                }
                else if (!isRoot) {
                    nodeIds.push(boundary['value']);
                    if (boundary['children'].length > 0) {
                        nodeIds.push.apply(nodeIds, self.getNodesWithoutChildren(boundary['children'], idsArray));
                    }
                }
            });
            return nodeIds;
        },
        whenPoliticalRegionBoundariesReady: function (callback) {
            var self = this;
            if (Shared.PoliticalRegionBoundaries) {
                callback();
            } else {
                setTimeout(function () {
                    self.whenPoliticalRegionBoundariesReady(callback);
                }, 500)
            }
        },
        getRegions: function (ids) {
            var nodeIds = this.getNodesWithoutChildren(
                Shared.PoliticalRegionBoundaries,
                ids,
                true);

            this.politicalRegionXHR = $.get({
                url: this.catchmentAreaBoundaryUrl + JSON.stringify(nodeIds),
                dataType: 'json',
                success: function (data) {
                    console.log('data', data);
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

                            console.log('olfeature', olfeature);

                            for (var i = 0; i < olfeature.length; i++) {
                                var id = 'adminArea-' + i + '-' + index;
                                olfeature[i].setProperties({'id': id});
                                Shared.AdminAreaSelected.push(id);
                            }

                            if (index === 0 && !isUserBoundaryDisplayed) {
                                console.log('switchHighlightPinned');
                                Shared.Dispatcher.trigger('map:switchHighlightPinned', olfeature, true);
                            } else {
                                console.log('addHighlightPinnedFeature');
                                Shared.Dispatcher.trigger('map:addHighlightPinnedFeature', olfeature[0]);
                            }
                        });
                        // Shared.Dispatcher.trigger('map:zoomToHighlightPinnedFeatures');
                    }
                },
                error: function () {
                    console.log('error');
                }
            });
        },
        show: function (ids) {
            var self = this;
            if (this.politicalRegionXHR) {
                this.politicalRegionXHR.abort();
            }
            this.whenPoliticalRegionBoundariesReady(function () {
                self.getRegions(ids)
            });
        }
    })
});
