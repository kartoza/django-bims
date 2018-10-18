define(['backbone', 'underscore', 'jquery', 'ol', 'olMapboxStyle'], function (Backbone, _, $, ol, OlMapboxStyle) {
    return Backbone.View.extend({
        getVectorTileMapBoxStyle: function (url, styleUrl, layerName, attributions) {
            var tilegrid = ol.tilegrid.createXYZ({tileSize: 512, maxZoom: 14});
            var layer = new ol.layer.VectorTile({
                source: new ol.source.VectorTile({
                    attributions: attributions,
                    format: new ol.format.MVT(),
                    tileGrid: tilegrid,
                    tilePixelRatio: 8,
                    url: url
                })
            });
            fetch(styleUrl).then(function (response) {
                response.json().then(function (glStyle) {
                    OlMapboxStyle.applyStyle(layer, glStyle, layerName).then(function () {
                    });
                });
            });
            return layer
        },
        getOpenMapTilesTile: function (styleUrl) {
            var attributions = '© <a href="https://openmaptiles.org/">OpenMapTiles</a> ' +
                '© <a href="http://www.openstreetmap.org/copyright">' +
                'OpenStreetMap contributors</a>';
            return this.getVectorTileMapBoxStyle(
                'https://maps.tilehosting.com/data/v3/{z}/{x}/{y}.pbf.pict?key=' + mapTilerKey,
                styleUrl,
                'openmaptiles',
                attributions
            );
        },
        getKlokantechTerrainBasemap: function () {
            var attributions = '© <a href="https://openmaptiles.org/">OpenMapTiles</a> ' +
                '© <a href="http://www.openstreetmap.org/copyright">' +
                'OpenStreetMap contributors</a>';
            var openMapTiles = this.getOpenMapTilesTile('/static/mapbox-style/klokantech-terrain-gl-style.json');
            var contours = this.getVectorTileMapBoxStyle(
                'https://maps.tilehosting.com/data/contours/{z}/{x}/{y}.pbf.pict?key=' + mapTilerKey,
                '/static/mapbox-style/klokantech-terrain-gl-style.json',
                'contours',
                attributions
            );
            var hillshading = new ol.layer.Tile({
                opacity: 0.1,
                source: new ol.source.XYZ({
                    url: 'https://maps.tilehosting.com/data/hillshades/{z}/{x}/{y}.png?key=' + mapTilerKey
                })
            });
            return new ol.layer.Group({
                title: 'Terrain',
                layers: [openMapTiles, hillshading, contours]
            });
        },
        getPositronBasemap: function () {
            var layer = this.getOpenMapTilesTile(
                '/static/mapbox-style/positron-gl-style.json');
            layer.set('title', 'Positron Map');
            return layer
        },
        getDarkMatterBasemap: function () {
            var layer = this.getOpenMapTilesTile(
                '/static/mapbox-style/dark-matter-gl-style.json');
            layer.set('title', 'Dark Matter');
            return layer
        },
        getBaseMaps: function () {
            var baseDefault = null;
            var baseSourceLayers = [];

            // TOPOSHEET MAP
            var toposheet = new ol.layer.Tile({
                title: 'Topography',
                source: new ol.source.XYZ({
                    attributions: ['&copy; National Geo-spatial Information (NGI) contributors', 'Toposheets'],
                    url: 'https://htonl.dev.openstreetmap.org/ngi-tiles/tiles/50k/{z}/{x}/{-y}.png'
                })
            });
            baseSourceLayers.push(toposheet);


            // NGI MAP
            var ngiMap = new ol.layer.Tile({
                title: 'Aerial photography',
                source: new ol.source.XYZ({
                    attributions: ['&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors', 'NGI'],
                    url: 'http://aerial.openstreetmap.org.za/ngi-aerial/{z}/{x}/{y}.jpg'
                })
            });
            baseSourceLayers.push(ngiMap);
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

            // OSM MAPSURFER ROADS - Make default
            var mapSurfer = new ol.layer.Tile({
                title: 'OSM Mapsurfer roads',
                source: new ol.source.XYZ({
                    attributions: ['&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'],
                    url: 'https://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}'
                })
            });
            baseSourceLayers.push(mapSurfer);

            // OPENMAPTILES
            if (mapTilerKey) {
                baseSourceLayers.push(this.getPositronBasemap());
                baseSourceLayers.push(this.getDarkMatterBasemap());
                baseSourceLayers.push(this.getKlokantechTerrainBasemap());
            }
            $.each(baseSourceLayers, function (index, layer) {
                layer.set('type', 'base');
                layer.set('visible', true);
                layer.set('preload', Infinity);
            });

            return baseSourceLayers
        }
    })
});
