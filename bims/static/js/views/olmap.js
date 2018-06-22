define([
    'backbone',
    'underscore',
    'shared',
    'collections/location_site',
    'collections/cluster',
    'collections/cluster_biological',
    'views/map_control_panel',
    'views/side_panel',
    'ol',
    'jquery', 'layerSwitcher', 'olMapboxStyle'], function (Backbone, _, Shared, LocationSiteCollection, ClusterCollection, ClusterBiologicalCollection, MapControlPanelView, SidePanelView, ol, $, LayerSwitcher, OlMapboxStyle) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,
        locationSiteVectorSource: null,
        clusterSource: null,
        geocontextOverlay: null,
        previousZoom: 0,
        sidePanelView: null,
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
            Shared.Dispatcher.on('map:addClusterFeatures', this.addClusterFeatures, this);
            Shared.Dispatcher.on('map:zoomToCoordinates', this.zoomToCoordinates, this);
            this.locationSiteCollection = new LocationSiteCollection();
            this.clusterCollection = new ClusterCollection();
            this.clusterBiologicalCollection = new ClusterBiologicalCollection();
            Shared.Dispatcher.on('searchResult:clicked', this.updateClusterBiologicalCollectionTaxonID, this);
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
        zoomToCoordinates: function (coordinates, zoomLevel) {
            this.map.getView().setCenter(coordinates);
            if (typeof zoomLevel !== 'undefined') {
                this.map.getView().setZoom(zoomLevel);
            }
        },
        mapClicked: function (e) {
            var self = this;
            var features = self.map.getFeaturesAtPixel(e.pixel);
            if (features) {
                var geometry = features[0].getGeometry();
                var geometryType = geometry.getType();
                if (geometryType === 'Point') {
                    self.featureClicked(features[0]);
                    var coordinates = geometry.getCoordinates();
                    self.zoomToCoordinates(coordinates);
                } else {
                    this.sidePanelView.closeSidePanel();
                }
            }
            else {
                this.sidePanelView.closeSidePanel();
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
        fetchingStart: function () {
            $('#loading-warning').show();

        },
        fetchingFinish: function () {
            $('#loading-warning').hide();

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
        getCurrentZoom: function () {
            return this.map.getView().getZoom();
        },
        getCurrentBbox: function () {
            var ext = this.map.getView().calculateExtent(this.map.getSize());
            return ol.proj.transformExtent(ext, ol.proj.get('EPSG:3857'), ol.proj.get('EPSG:4326'));
        },
        render: function () {
            var self = this;

            this.$el.html(this.template());
            $('#map-container').append(this.$el);
            this.loadMap();

            this.map.on('click', function (e) {
                self.mapClicked(e);
            });

            this.sidePanelView = new SidePanelView();

            this.mapControlPanel = new MapControlPanelView({
                parent: this
            });

            this.$el.append(this.mapControlPanel.render().$el);
            this.$el.append(this.sidePanelView.render().$el);

            // add layer switcher
            var layerSwitcher = new LayerSwitcher();
            this.map.addControl(layerSwitcher);
            this.map.on('moveend', function (evt) {
                self.mapMoved();
            });

            return this;
        },
        mapMoved: function () {
            var self = this;
            self.updateClusterBiologicalCollectionZoomExt();
            self.fetchingRecords();
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


            // cluster layer
            self.clusterSource = new ol.source.Vector({});

            var styleFunction = function (feature) {
                var count = 1;
                if (feature.getProperties()['count']) {
                    count = feature.getProperties()['count'];
                }
                var style = self.getClusterStyle(count);
                style.getText().setText('' + count);
                return style;
            };

            var clusterVectorLayer = new ol.layer.Vector({
                source: self.clusterSource,
                style: styleFunction
            });
            this.map.addLayer(clusterVectorLayer);
        },
        fetchingRecords: function () {
            // get records based on administration
            var self = this;
            if (this.fetchXhr) {
                this.fetchXhr.abort();
            }
            if (!this.clusterBiologicalCollection.taxonID) {
                var administrative = this.checkAdministrativeLevel();
                if (administrative !== 'detail') {
                    this.locationSiteVectorSource.clear();
                    var zoomLevel = this.getCurrentZoom();
                    if (administrative === this.clusterCollection.administrative) {
                        return
                    }
                    if (zoomLevel === this.previousZoom) {
                        return
                    }
                    this.previousZoom = zoomLevel;
                    this.clusterCollection.updateUrl(administrative);
                    this.fetchingStart();
                    this.fetchXhr = this.clusterCollection.fetch({
                        success: function () {
                            self.fetchingFinish();
                            self.clusterSource.clear();
                            self.locationSiteVectorSource.clear();
                            self.clusterCollection.renderCollection()
                        }
                    });
                } else {
                    this.clusterSource.clear();
                    this.fetchingStart();
                    this.locationSiteCollection.updateUrl(this.getCurrentBbox());
                    this.fetchXhr = this.locationSiteCollection.fetch({
                        success: function () {
                            self.fetchingFinish();
                            self.clusterSource.clear();
                            self.locationSiteVectorSource.clear();
                            self.locationSiteCollection.renderCollection()
                        }
                    });
                }
            } else {
                this.fetchingStart();
                this.locationSiteVectorSource.clear();
                this.fetchXhr = this.clusterBiologicalCollection.fetch({
                    success: function () {
                        self.fetchingFinish();
                        self.clusterSource.clear();
                        self.locationSiteVectorSource.clear();
                        self.clusterBiologicalCollection.renderCollection();
                    }
                });
            }
        },
        updateClusterBiologicalCollectionTaxonID: function (taxonID) {
            if (!this.sidePanelView.isSidePanelOpen()) {
                return
            }
            if (!taxonID && !this.clusterBiologicalCollection.taxonID) {
                return
            }
            this.clusterBiologicalCollection.updateTaxon(taxonID);
            if (!this.clusterBiologicalCollection.taxonID) {
                // clear all data for taxon records
                this.clusterSource.clear();
                this.previousZoom = -1;
                this.clusterCollection.administrative = null;
                this.fetchingRecords();
            } else {
                // get extent for all record and fit it to map
                var self = this;
                $.ajax({
                    url: '/api/cluster/collection/taxon/' + taxonID + '/extent/',
                    dataType: "json",
                    success: function (data) {
                        if (data.length == 4) {
                            // after fit to map, show the cluster
                            var ext = ol.proj.transformExtent(data, ol.proj.get('EPSG:4326'), ol.proj.get('EPSG:3857'));
                            self.map.getView().fit(ext, {
                                size: self.map.getSize(), padding: [
                                    0, $('.right-panel').width(), 0, 0
                                ]
                            });
                        }
                    }
                });
            }
        },
        updateClusterBiologicalCollectionZoomExt: function () {
            this.clusterBiologicalCollection.updateZoomAndBBox(this.getCurrentZoom(), this.getCurrentBbox());
        },
        getClusterStyle: function (count) {
            var smallCluster = new ol.style.Circle({
                radius: 15,
                fill: new ol.style.Fill({
                    color: 'red'
                })
            });
            var mediumCluster = new ol.style.Circle({
                radius: 30,
                fill: new ol.style.Fill({
                    color: 'yellow'
                })
            });
            var largeCluster = new ol.style.Circle({
                radius: 45,
                fill: new ol.style.Fill({
                    color: 'green'
                })
            });
            var image = null;
            if (count < 10) {
                image = smallCluster;
            } else if (10 >= count <= 100) {
                image = mediumCluster;
            } else {
                image = largeCluster
            }
            return new ol.style.Style({
                image: image,
                text: new ol.style.Text({
                    scale: 1,
                    fill: new ol.style.Fill({
                        color: '#000000'
                    })
                })
            });
        },
        addLocationSiteFeatures: function (features) {
            this.locationSiteVectorSource.addFeatures(features);
        },
        addClusterFeatures: function (features) {
            this.clusterSource.addFeatures(features);
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
