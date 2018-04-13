define(['backbone', 'models/location_site', 'openlayers'], function (Backbone, LocationSite, ol) {
   return Backbone.View.extend({
        initialize: function (options) {
            this.parent = options.parent;
            _.bindAll(this, 'render');
            this.model.fetch({
                success: this.render
            });
        },
        render: function () {
            var modelJson = this.model.toJSON();
            var geometry = JSON.parse(modelJson['geometry']);
            delete modelJson['geometry'];
            var geojson = {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': geometry,
                        'properties': modelJson
                    }
                ]
            };

            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                    anchor: [0.5, 46],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 0.75,
                    src: 'static/img/marker.png'
                }))
            });

            var features = new ol.format.GeoJSON().readFeatures(geojson, {
                featureProjection: 'EPSG:3857'
            });

            this.parent.addLocationSiteFeatures(features);
        }
   })
});
