define([
    'backbone',
    'underscore',
    'shared',
    'collections/location_site',
    'collections/cluster',
    'views/map_control_panel',
    'ol',
    'jquery', 'layerSwitcher', 'olMapboxStyle'], function (Backbone, _, Shared, LocationSiteCollection, ClusterCollection, MapControlPanelView, ol, $, LayerSwitcher, OlMapboxStyle) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,
        locationSiteVectorSource: null,
        geocontextOverlay: null,
        previousZoom: 0,
        geocontextOverlayDisplayed: false,
        events: {
            'click .zoom-in': 'zoomInMap',
            'click .zoom-out': 'zoomOutMap',
            'click .layer-control': 'layerControlClicked'
        },
        clusterLevel: {
            5: 'country',
            7: 'province',
            8: 'district',
            9: 'municipal'
        }, // note that this is the max level for cluster level
        initialize: function () {
            // Ensure methods keep the `this` references to the view itself
            _.bindAll(this, 'render');
            Shared.Dispatcher.on('map:addLocationSiteFeatures', this.addLocationSiteFeatures, this);
            this.locationSiteCollection = new LocationSiteCollection();
            this.clusterCollection = new ClusterCollection();
            this.render();
        },
        zoomInMap: function (e) {
            var view = this.map.getView();
            var zoom = view.getZoom();
            view.animate({
                zoom: zoom - 1,
                duration: 250
            })
        },
        zoomOutMap: function (e) {
            var view = this.map.getView();
            var zoom = view.getZoom();
            view.animate({
                zoom: zoom + 1,
                duration: 250
            })
        },
        mapClicked: function (e) {
            var self = this;
            var features = self.map.getFeaturesAtPixel(e.pixel);

            if (features) {
                self.featureClicked(features[0]);
            } else {
                Shared.Dispatcher.trigger('sidePanel:closeSidePanel');
            }

            // Close opened control panel
            this.mapControlPanel.closeAllPanel();

            if (this.mapControlPanel.locationControlActive) {
                if (this.geocontextOverlayDisplayed === false) {
                    this.showGeoContext(e.coordinate);
                } else {
                    this.hideGeoContext();
                }
            }
        },
        hideGeoContext: function () {
            this.geoOverlayContent.innerHTML = '';
            this.geocontextOverlay.setPosition(undefined);
            this.geocontextOverlayDisplayed = false;
        },
        showGeoContext: function (coordinate) {

            if (!geocontextUrl) {
                return false;
            }

            this.geocontextOverlayDisplayed = true;

            var lonlat = ol.proj.transform(coordinate, "EPSG:3857", "EPSG:4326");

            // Show popup
            var hdms = ol.coordinate.toStringHDMS(ol.proj.transform(
                coordinate, "EPSG:3857", "EPSG:4326"
            ));

            this.geoOverlayContent.innerHTML = '<div class=small-loading></div>';
            this.geocontextOverlay.setPosition(coordinate);
            var lon = lonlat[0];
            var lan = lonlat[1];
            var self = this;

            var url = geocontextUrl + "/geocontext/value/list/" + lon + "/" + lan + "/?with-geometry=False";

            $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    var contentDiv = '<div>';
                    for (var i = 0; i < data.length; i++) {
                        contentDiv += data[i]['display_name'] + ' : ' + data[i]['value'];
                        contentDiv += '<br>';
                    }
                    contentDiv += '</div>';
                    self.geoOverlayContent.innerHTML = contentDiv;
                },
                error: function (req, err) {
                    console.log(err);
                }
            });
        },
        featureClicked: function (feature) {
            var properties = feature.getProperties();
            Shared.Dispatcher.trigger('locationSite-' + properties.id + ':clicked');
        },
        layerControlClicked: function (e) {
        },
        checkAdministrativeLevel: function () {
            var self = this;
            var zoomLevel = this.map.getView().getZoom();
            var administrative = 'detail';
            $.each(Object.keys(this.clusterLevel), function (index, value) {
                if (zoomLevel <= value) {
                    administrative = self.clusterLevel[value];
                    return false;
                }
            });
            return administrative;
        },
        refetchCollection: function () {
            var self = this;
            var administrative = this.checkAdministrativeLevel();
            if (administrative != 'detail') {
                this.clusterCollection.updateAdministrative(administrative);
                this.clusterCollection.fetch({
                    success: function () {
                        self.locationSiteVectorSource.clear();
                        self.clusterCollection.renderCollection()
                    }
                });
            } else {
                this.locationSiteCollection.fetch({
                    success: function () {
                        self.locationSiteVectorSource.clear();
                        self.locationSiteCollection.renderCollection()
                    }
                });
            }

        },
        render: function () {
            var self = this;

            this.$el.html(this.template());
            $('#map-container').append(this.$el);
            this.loadMap();
            self.refetchCollection();

            this.map.on('click', function (e) {
                self.mapClicked(e);
            });

            this.mapControlPanel = new MapControlPanelView({
                parent: this
            });

            this.$el.append(this.mapControlPanel.render().$el);

            // add layer switcher
            var layerSwitcher = new LayerSwitcher();
            this.map.addControl(layerSwitcher);

            this.previousZoom = self.map.getView().getZoom();

            this.map.on('moveend', function (evt) {
                var zoomLevel = self.map.getView().getZoom();
                if (zoomLevel !== self.previousZoom) {
                    self.previousZoom = zoomLevel;
                    self.refetchCollection();
                }
                var ext = self.map.getView().calculateExtent(self.map.getSize())
                ext = ol.proj.transformExtent(ext, ol.proj.get('EPSG:3857'), ol.proj.get('EPSG:4326'));
                console.log('http://localhost:63302/api/cluster-module/?icon_pixel_x=30&icon_pixel_y=30&module=fish' + '&zoom=' + self.map.getView().getZoom() + '&bbox=' + ext);
            });
            return this;
        },
        loadMap: function () {
            var self = this;

            self.locationSiteVectorSource = new ol.source.Vector({});

            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                    anchor: [0.5, 46],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 0.75,
                    src: 'static/img/map-marker.png'
                })),
                text: new ol.style.Text({
                    scale: 1,
                    fill: new ol.style.Fill({
                        color: '#000000'
                    })
                })
            });

            var styles = {
                'Point': iconStyle,
                'LineString': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'green',
                        width: 1
                    })
                }),
                'MultiPolygon': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'yellow',
                        width: 1
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 0, 0.1)'
                    })
                }),
                'Polygon': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'blue',
                        lineDash: [4],
                        width: 3
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(0, 0, 255, 0.1)'
                    })
                })
            };

            var styleFunction = function (feature) {
                var style = styles[feature.getGeometry().getType()];
                if (feature.getProperties()['text']) {
                    style.getText().setText(feature.getProperties()['text'])
                }
                return style;
            };

            var locationSiteVectorLayer = new ol.layer.Vector({
                source: self.locationSiteVectorSource,
                style: styleFunction
            });

            this.geoOverlayContainer = document.getElementById('geocontext-popup');
            this.geoOverlayContent = document.getElementById('geocontext-content');
            this.geoOverlayCloser = document.getElementById('geocontext-closer');

            this.geocontextOverlay = new ol.Overlay({
                element: this.geoOverlayContainer,
                autoPan: true,
                autoPanAnimation: {
                    duration: 250
                }
            });

            this.geoOverlayCloser.onclick = function () {
                self.geocontextOverlay.setPosition(undefined);
                self.geoOverlayCloser.blur();
                return false;
            };

            this.map = new ol.Map({
                target: 'map',
                layers: self.getBaseMaps(),
                view: new ol.View({
                    center: ol.proj.fromLonLat([22.937506, -30.559482]),
                    zoom: 7
                }),
                controls: ol.control.defaults({
                    zoom: false
                }),
                overlays: [this.geocontextOverlay]
            });
            this.map.addLayer(locationSiteVectorLayer);
        },
        addLocationSiteFeatures: function (features) {
            this.locationSiteVectorSource.addFeatures(features);
        },

        // TODO : When this functions moved to other js, the mapbox style broken (doesn't call style)
        // ------------------------------ BASEMAP ---------------------------------
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
            var openMapTiles = this.getOpenMapTilesTile(staticURL + 'mapbox-style/klokantech-terrain-gl-style.json');
            var contours = this.getVectorTileMapBoxStyle(
                'https://maps.tilehosting.com/data/contours/{z}/{x}/{y}.pbf.pict?key=' + mapTilerKey,
                staticURL + 'mapbox-style/klokantech-terrain-gl-style.json',
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
                title: 'Klokantech Terrain',
                layers: [openMapTiles, hillshading, contours]
            });
        },
        getPositronBasemap: function () {
            var layer = this.getOpenMapTilesTile(
                staticURL + 'mapbox-style/positron-gl-style.json');
            layer.set('title', 'Positron Map');
            return layer
        },
        getDarkMatterBasemap: function () {
            var layer = this.getOpenMapTilesTile(
                staticURL + 'mapbox-style/dark-matter-gl-style.json');
            layer.set('title', 'Dark Matter');
            return layer
        },
        getBaseMaps: function () {
            var baseDefault = null;
            var baseSourceLayers = [];

            // TOPOSHEET MAP
            var toposheet = new ol.layer.Tile({
                title: 'South Africa 1:50k Toposheets',
                source: new ol.source.XYZ({
                    attributions: ['&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors', 'Toposheets'],
                    url: 'https://htonl.dev.openstreetmap.org/ngi-tiles/tiles/50k/{z}/{x}/{-y}.png'
                })
            });
            baseSourceLayers.push(toposheet);


            // NGI MAP
            var ngiMap = new ol.layer.Tile({
                title: 'NGI OSM aerial photographs',
                source: new ol.source.XYZ({
                    attributions: ['&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors', 'NGI'],
                    url: 'http://aerial.openstreetmap.org.za/ngi-aerial/{z}/{x}/{y}.jpg'
                })
            });
            baseSourceLayers.push(ngiMap);
            // add bing
            if (bingMapKey) {
                var bingMap = new ol.layer.Tile({
                    title: 'Bing',
                    source: new ol.source.BingMaps({
                        key: bingMapKey,
                        imagerySet: 'AerialWithLabels'
                    })
                });
                baseSourceLayers.push(bingMap);
            }

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
