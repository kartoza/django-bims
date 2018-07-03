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
        biodiversitySource: null,
        highlightVectorSource: null,

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
            Shared.Dispatcher.on('map:addBiodiversityFeatures', this.addBiodiversityFeatures, this);
            Shared.Dispatcher.on('map:updateAdministrativeBoundary', this.updateAdministrativeBoundaryFeatures, this);
            Shared.Dispatcher.on('map:zoomToCoordinates', this.zoomToCoordinates, this);
            Shared.Dispatcher.on('map:zoomToExtent', this.zoomToExtent, this);
            Shared.Dispatcher.on('map:reloadXHR', this.reloadXHR, this);
            Shared.Dispatcher.on('map:showPopup', this.showPopup, this);
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
        zoomToExtent: function (coordinates) {
            var ext = ol.proj.transformExtent(coordinates, ol.proj.get('EPSG:4326'), ol.proj.get('EPSG:3857'));
            this.map.getView().fit(ext, {
                size: this.map.getSize(), padding: [
                    0, $('.right-panel').width(), 0, 0
                ]
            });
        },
        mapClicked: function (e) {
            var self = this;
            var features = self.map.getFeaturesAtPixel(e.pixel);
            this.highlightVectorSource.clear();
            this.hidePopup();
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
                }
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
            if (properties['record_type'] === 'site') {
                Shared.Dispatcher.trigger('locationSite-' + properties.id + ':clicked');
            } else {
                Shared.Dispatcher.trigger('cluster-biology' + properties.id + ':clicked');
            }
            this.highlightVectorSource.clear();
            if (!properties['count'] || properties['count'] === 1) {
                this.addHighlightFeature(feature);
            }
        },
        hidePopup: function () {
            this.popup.setPosition(undefined);
        },
        showPopup: function (coordinates, html) {
            $('#popup').html(html);
            this.popup.setPosition(coordinates);
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
            this.biodiversitySource.clear();
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
                target: document.getElementById('mouse-position-wrapper'),
                coordinateFormat: function (coordinate) {
                    return ol.coordinate.format(coordinate, '{y},{x}', 4);
                }
            });
            var basemap = new Basemap();
            this.map = new ol.Map({
                target: 'map',
                layers: basemap.getBaseMaps(),
                view: new ol.View({
                    center: ol.proj.fromLonLat([22.937506, -30.559482]),
                    zoom: 7,
                    minZoom: 7,
                    extent: [1801862.6258878047, -4051414.739574095, 3304920.3500875104, -3099926.6114802207]
                }),
                controls: ol.control.defaults({
                    zoom: false
                }).extend([mousePositionControl]),
                overlays: [this.geocontextOverlay]
            });

            // Create a popup overlay which will be used to display feature info
            this.popup = new ol.Overlay({
                element: document.getElementById('popup'),
                positioning: 'bottom-center',
                offset: [0, -55]
            });
            this.map.addOverlay(this.popup);

            // BIODIVERSITY LAYERS
            // ---------------------------------
            self.biodiversitySource = new ol.source.Vector({});
            this.map.addLayer(new ol.layer.Vector({
                source: self.biodiversitySource,
                style: function (feature) {
                    return self.layerStyle.getBiodiversityStyle(feature);
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

            // highlight layer
            // ---------------------------------
            self.highlightVectorSource = new ol.source.Vector({});
            this.map.addLayer(new ol.layer.Vector({
                source: self.highlightVectorSource,
                style: function (feature) {
                    var geom = feature.getGeometry();
                    return self.layerStyle.getHighlightStyle(geom.getType());
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
            if (!this.clusterBiologicalCollection.getTaxon()) {
                var administrative = this.checkAdministrativeLevel();
                if (administrative !== 'detail') {
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
                        this.biodiversitySource.clear();
                        this.clusterCollection.applyCache();
                    } else {
                        this.fetchingStart();
                        this.fetchXhr = this.clusterCollection.fetch({
                            success: function () {
                                self.fetchingFinish();
                                self.clusterCollection.renderCollection()
                            }, error: function () {
                                self.fetchingError();
                            }
                        });
                    }
                } else {
                    this.previousZoom = -1;
                    this.clusterCollection.administrative = null;
                    this.administrativeBoundarySource.clear();
                    this.fetchingReset();
                    this.fetchingStart();
                    this.locationSiteCollection.updateUrl(this.getCurrentBbox());
                    this.fetchXhr = this.locationSiteCollection.fetch({
                        success: function () {
                            self.fetchingFinish();
                            self.locationSiteCollection.renderCollection()
                        }, error: function () {
                            self.fetchingError();
                        }
                    });
                }
            } else {
                this.fetchingReset();
                this.fetchingStart();
                this.biodiversitySource.clear();
                this.administrativeBoundarySource.clear();
                this.fetchXhr = this.clusterBiologicalCollection.fetch({
                    success: function () {
                        self.fetchingFinish();
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
            if (!taxonID && !this.clusterBiologicalCollection.getTaxon()) {
                return
            }
            this.clusterBiologicalCollection.updateTaxon(taxonID);
            if (!this.clusterBiologicalCollection.getTaxon()) {
                this.previousZoom = -1;
                this.clusterCollection.administrative = null;
                this.fetchingRecords();
            } else {
                this.clusterBiologicalCollection.getExtentOfRecords();
            }
        },
        updateClusterBiologicalCollectionZoomExt: function () {
            this.clusterBiologicalCollection.updateZoomAndBBox(this.getCurrentZoom(), this.getCurrentBbox());
        },
        addBiodiversityFeatures: function (features) {
            this.biodiversitySource.addFeatures(features);
        },
        addHighlightFeature: function (feature) {
            this.highlightVectorSource.addFeature(feature);
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
    })
});
