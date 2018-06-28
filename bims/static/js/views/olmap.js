define([
    'backbone',
    'underscore',
    'shared',
    'collections/location_site',
    'collections/cluster',
    'collections/cluster_biological',
    'views/map_control_panel',
    'views/side_panel',
    'views/boundary',
    'ol',
    'jquery', 'layerSwitcher',
    'views/basemap', 'views/layer_style'], function (Backbone, _, Shared, LocationSiteCollection, ClusterCollection, ClusterBiologicalCollection,
                                                     MapControlPanelView, SidePanelView, BoundaryView, ol, $, LayerSwitcher, Basemap, LayerStyle) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,

        // source of layers
        administrativeBoundarySource: null,
        clusterSource: null,
        locationSiteVectorSource: null,

        // attributes
        geocontextOverlay: null,
        geocontextOverlayDisplayed: false,
        mapInteractionEnabled: true,
        previousZoom: 0,
        sidePanelView: null,
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
            Shared.Dispatcher.on('map:updateAdministrativeBoundary', this.updateAdministrativeBoundaryFeatures, this);
            Shared.Dispatcher.on('map:zoomToCoordinates', this.zoomToCoordinates, this);
            Shared.Dispatcher.on('map:reloadXHR', this.reloadXHR, this);
            this.layerStyle = new LayerStyle();
            this.boundaryView = new BoundaryView();
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

                    // increase zoom level if it is clusters
                    if (features[0].getProperties()['count']) {
                        self.map.getView().setZoom(self.getCurrentZoom() + 1);
                    }
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
            $('#fetching-error').hide();
            $('#loading-warning').show();
            if (this.fetchXhr) {
                this.fetchXhr.abort();
            }
            this.mapInteractionEnabled = false;
            this.map.getInteractions().forEach(function (interaction) {
                interaction.setActive(false);
            });
        },
        fetchingFinish: function () {
            this.fetchingReset();
            this.mapInteractionEnabled = true;
            this.map.getInteractions().forEach(function (interaction) {
                interaction.setActive(true);
            });
        },
        fetchingError: function () {
            $('#fetching-error').show();
            $('#loading-warning').hide();
            this.mapInteractionEnabled = true;
            this.map.getInteractions().forEach(function (interaction) {
                interaction.setActive(true);
            });
        },
        fetchingReset: function () {
            $('#fetching-error').hide();
            $('#loading-warning').hide();
            $('#fetching-error .call-administrator').hide();
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

            var mousePositionControl = new ol.control.MousePosition({
                coordinateFormat: ol.coordinate.createStringXY(4),
                projection: 'EPSG:4326',
                target: document.getElementById('page-top'),
                className: 'mouse-position',
                undefinedHTML: '&nbsp;',
                coordinateFormat: function (coordinate) {
                    return ol.coordinate.format(coordinate, '{y}, {x}', 4);
                }
            });
            this.map = new ol.Map({
                target: 'map',
                layers: self.getBaseMaps(),
                view: new ol.View({
                    center: ol.proj.fromLonLat([22.937506, -30.559482]),
                    zoom: 7
                }),
                controls: ol.control.defaults({
                    zoom: false
                }).extend([mousePositionControl]),
                overlays: [this.geocontextOverlay]
            });

            // LOAD SOURCE LAYERS
            // ---------------------------------
            self.locationSiteVectorSource = new ol.source.Vector({});
            this.map.addLayer(new ol.layer.Vector({
                source: self.locationSiteVectorSource,
                style: function (feature) {
                    return self.layerStyle.getSiteStyle(feature.getGeometry().getType());
                }
            }));

            // Administrative boundary layer
            // ---------------------------------
            self.administrativeBoundarySource = new ol.source.Vector({});
            this.map.addLayer(new ol.layer.Vector({
                source: self.administrativeBoundarySource,
                style: function (feature) {
                    return new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'yellow',
                            width: 1
                        }),
                        text: new ol.style.Text({
                            scale: 1,
                            fill: new ol.style.Fill({
                                color: '#000000'
                            }),
                            text: feature.getProperties()['name']
                        })
                    })
                }
            }));

            // cluster layer
            // ---------------------------------
            self.clusterSource = new ol.source.Vector({});
            this.map.addLayer(new ol.layer.Vector({
                source: self.clusterSource,
                style: function (feature) {
                    var count = 1;
                    if (feature.getProperties()['count']) {
                        count = feature.getProperties()['count'];
                    }
                    var style = self.layerStyle.getClusterStyle(count);
                    style.getText().setText('' + count);
                    return style;
                }
            }));
            this.startOnHoverListener();
        },
        reloadXHR: function () {
            this.previousZoom = -1;
            this.clusterCollection.administrative = null;
            this.fetchingRecords();
            $('#fetching-error .call-administrator').show();
        },
        fetchingRecords: function () {
            // get records based on administration
            var self = this;
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
                    this.fetchingReset();
                    // generate boundary
                    this.administrativeBoundarySource.clear();
                    this.boundaryView.renderAdministrativeBoundary(
                        administrative, this.getCurrentBbox());

                    this.previousZoom = zoomLevel;
                    this.clusterCollection.updateUrl(administrative);
                    if (this.clusterCollection.getCache()) {
                        this.clusterSource.clear();
                        this.locationSiteVectorSource.clear();
                        this.clusterCollection.applyCache();
                    } else {
                        this.fetchingStart();
                        this.fetchXhr = this.clusterCollection.fetch({
                            success: function () {
                                self.fetchingFinish();
                                self.clusterSource.clear();
                                self.locationSiteVectorSource.clear();
                                self.clusterCollection.renderCollection()
                            }, error: function () {
                                self.fetchingError();
                            }
                        });
                    }
                } else {
                    this.previousZoom = -1;
                    this.clusterCollection.administrative = null;
                    this.clusterSource.clear();
                    this.administrativeBoundarySource.clear();
                    this.fetchingReset();
                    this.fetchingStart();
                    this.locationSiteCollection.updateUrl(this.getCurrentBbox());
                    this.fetchXhr = this.locationSiteCollection.fetch({
                        success: function () {
                            self.fetchingFinish();
                            self.clusterSource.clear();
                            self.locationSiteVectorSource.clear();
                            self.locationSiteCollection.renderCollection()
                        }, error: function () {
                            self.fetchingError();
                        }
                    });
                }
            } else {
                this.fetchingReset();
                this.fetchingStart();
                this.locationSiteVectorSource.clear();
                this.administrativeBoundarySource.clear();
                this.fetchXhr = this.clusterBiologicalCollection.fetch({
                    success: function () {
                        self.fetchingFinish();
                        self.clusterSource.clear();
                        self.locationSiteVectorSource.clear();
                        self.clusterBiologicalCollection.renderCollection();
                    }, error: function () {
                        self.fetchingError();
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
        addLocationSiteFeatures: function (features) {
            this.locationSiteVectorSource.addFeatures(features);
        },
        addClusterFeatures: function (features) {
            this.clusterSource.addFeatures(features);
        },
        updateAdministrativeBoundaryFeatures: function (features) {
            this.administrativeBoundarySource.addFeatures(features);
        },
        startOnHoverListener: function () {
            var that = this;
            this.pointerMoveListener = this.map.on('pointermove', function (e) {
                var pixel = that.map.getEventPixel(e.originalEvent);
                var hit = that.map.hasFeatureAtPixel(pixel);
                $('#' + that.map.getTarget()).find('canvas').css('cursor', 'move');
                if (hit) {
                    that.map.forEachFeatureAtPixel(pixel,
                        function (feature, layer) {
                            if (feature.getGeometry().getType() == 'Point') {
                                $('#' + that.map.getTarget()).find('canvas').css('cursor', 'pointer');
                            }
                        })
                }
            });
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
            var basemap = new Basemap();
            if (mapTilerKey) {
                baseSourceLayers.push(basemap.getPositronBasemap());
                baseSourceLayers.push(basemap.getDarkMatterBasemap());
                baseSourceLayers.push(basemap.getKlokantechTerrainBasemap());
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
