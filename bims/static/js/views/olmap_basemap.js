define(['backbone', 'underscore', 'jquery', 'ol', 'olMapboxStyle'], function (Backbone, _, $, ol, OlMapboxStyle) {
    return Backbone.View.extend({
        getVectorTileMapBoxStyle: function (url, styleUrl, layerName, attributions) {
            let tileGrid = ol.tilegrid.createXYZ({tileSize: 512, maxZoom: 14});
            let layer = new ol.layer.VectorTile({
                source: new ol.source.VectorTile({
                    attributions: attributions,
                    format: new ol.format.MVT(),
                    tileGrid: tileGrid,
                    tilePixelRatio: 8,
                    url: url
                })
            });
            if (styleUrl) {
                fetch(styleUrl).then(function (response) {
                    response.json().then(function (glStyle) {
                        OlMapboxStyle.applyStyle(layer, glStyle, layerName).then(function () {
                        });
                    });
                });
            }
            return layer;
        },
        getOpenMapTilesTile: function (styleUrl, attributions) {
            if (!attributions) {
                attributions = '© <a href="https://openmaptiles.org/">OpenMapTiles</a> ' +
                    '© <a href="http://www.openstreetmap.org/copyright">' +
                    'OpenStreetMap contributors</a>';
            }
            return this.getVectorTileMapBoxStyle(
                '/bims_proxy/https://api.maptiler.com/tiles/v3/{z}/{x}/{y}.pbf.pict?key=' + mapTilerKey,
                styleUrl,
                'openmaptiles',
                attributions
            );
        },
        getKlokantechTerrainBasemap: function () {
            var attributions = 'Data from <a href="http://www.openstreetmap.org/copyright">' +
                'OpenStreetMap</a> contributors; Tiles &copy; ' +
                '<a href="http://KlokanTech.com">KlokanTech</a>\n';
            var openMapTiles = this.getOpenMapTilesTile('/static/mapbox-style/klokantech-terrain-gl-style.json');
            return new ol.layer.Group({
                title: 'Terrain',
                layers: [openMapTiles,]
            });
        },
        getKartozaBaseMap: function () {
            let baseMapLayer = new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: '/bims_proxy/https://maps.kartoza.com/mapproxy/service',
                    params: {
                        'layers': 'basemap',
                        'uppercase': true,
                        'transparent': true,
                        'continuousWorld': true,
                        'opacity': 1.0,
                        'SRS': 'EPSG:3857'
                    }
                })
            });
            return new ol.layer.Group({
                title: 'Terrain',
                layers: [baseMapLayer,]
            });
        },
        getPositronBasemap: function () {
            var layer = this.getOpenMapTilesTile(
                '/static/mapbox-style/positron-gl-style.json',
                'Data from <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> ' +
                'contributors; Tiles &copy; <a href="http://carto.com/attributions#basemaps">Carto</a>\n'
                );
            layer.set('title', 'Plain greyscale');
            return layer
        },
        getDarkMatterBasemap: function () {
            var layer = this.getOpenMapTilesTile(
                '/static/mapbox-style/dark-matter-gl-style.json',
                'Data from <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> ' +
                'contributors; Tiles &copy; <a href="http://carto.com/attributions#basemaps">Carto</a>\n'
                );
            layer.set('title', 'Plain B&W');
            return layer
        },
        getBaseMaps: function () {
            var baseDefault = null;
            var baseSourceLayers = [];

            // TOPOSHEET MAP
            var toposheet = new ol.layer.Tile({
                title: 'Topography',
                source: new ol.source.XYZ({
                    attributions: ['Data &copy; <a href="http://www.ngi.gov.za/">' +
                    'National Geospatial Information (NGI)</a>; Tiles from ' +
                    '<a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'],
                    url: '/bims_proxy/https://htonl.dev.openstreetmap.org/ngi-tiles/tiles/50k/{z}/{x}/{-y}.png'
                })
            });

            // NGI MAP
            var ngiMap = new ol.layer.Tile({
                title: 'Aerial photography',
                source: new ol.source.XYZ({
                    attributions: ['<a href="http://www.ngi.gov.za/">CD:NGI Aerial</a>'],
                    url: '/bims_proxy/http://aerial.openstreetmap.org.za/ngi-aerial/{z}/{x}/{y}.jpg'
                })
            });

            // OPENMAPTILES
            if (mapTilerKey) {
                baseSourceLayers.push(this.getPositronBasemap());
                baseSourceLayers.push(this.getDarkMatterBasemap());
            }

            // add bing
            if (bingMapKey) {
                var bingMap = new ol.layer.Tile({
                    title: 'Bing Satellite Hybrid',
                    source: new ol.source.BingMaps({
                        key: bingMapKey,
                        imagerySet: 'AerialWithLabels'
                    })
                });
                baseSourceLayers.push(bingMap);
            }

            baseSourceLayers.push(ngiMap);

            if (mapSurferKey) {
                // OSM MAPSURFER ROADS - Make default
                var mapSurfer = new ol.layer.Tile({
                    title: 'OpenStreetMap',
                    source: new ol.source.XYZ({
                        attributions: ['Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @University of Heidelberg</a>; Map data from <a href="http://openstreetmap.org">OpenStreetMap</a> contributors; <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'],
                        url: '/bims_proxy/https://api.openrouteservice.org/mapsurfer/{z}/{x}/{y}.png?api_key=' + mapSurferKey
                    })
                });
                baseSourceLayers.push(mapSurfer);
            }
            baseSourceLayers.push(toposheet);

            baseSourceLayers.push(this.getKartozaBaseMap());

            $.each(baseSourceLayers, function (index, layer) {
                layer.set('type', 'base');
                layer.set('visible', true);
                layer.set('preload', Infinity);
            });

            return baseSourceLayers
        }
    })
});
