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
    'jquery',
    'layerSwitcher',
    'views/olmap_basemap',
    'views/olmap_layers',
    'views/geocontext'
    ], function (
        Backbone, _, Shared, LocationSiteCollection, ClusterCollection,
        ClusterBiologicalCollection, MapControlPanelView, SidePanelView,
        BoundaryView, ol, $, LayerSwitcher, Basemap, Layers, Geocontext
        ) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,

        // attributes
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
            this.layers = new Layers();
            this.boundaryView = new BoundaryView();
            this.locationSiteCollection = new LocationSiteCollection();
            this.clusterCollection = new ClusterCollection();
            this.geocontext = new Geocontext();

            Shared.Dispatcher.on('map:addBiodiversityFeatures', this.addBiodiversityFeatures, this);
            Shared.Dispatcher.on('map:updateAdministrativeBoundary', this.updateAdministrativeBoundaryFeatures, this);
            Shared.Dispatcher.on('map:zoomToCoordinates', this.zoomToCoordinates, this);
            Shared.Dispatcher.on('map:zoomToExtent', this.zoomToExtent, this);
            Shared.Dispatcher.on('map:reloadXHR', this.reloadXHR, this);
            Shared.Dispatcher.on('map:showPopup', this.showPopup, this);
            Shared.Dispatcher.on('map:closeHighlight', this.closeHighlight, this);
            Shared.Dispatcher.on('searchResult:updateTaxon', this.updateClusterBiologicalCollectionTaxonID, this);

            this.render();
            this.clusterBiologicalCollection = new ClusterBiologicalCollection(this.initExtent);
            this.mapControlPanel.searchView.initDateFilter();
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
            this.layers.highlightVectorSource.clear();
            this.hidePopup();
            if (features) {
                var geometry = features[0].getGeometry();
                var geometryType = geometry.getType();
                if (geometryType === 'Point') {
                    self.featureClicked(features[0]);
                    var coordinates = geometry.getCoordinates();
                    self.zoomToCoordinates(coordinates);

                    // increase zoom level if it is clusters
                    if (features[0].getProperties()['count'] &&
                        features[0].getProperties()['count'] > 1) {
                        self.map.getView().setZoom(self.getCurrentZoom() + 1);
                    }
                }
            }

            // Close opened control panel
            this.mapControlPanel.closeAllPanel();
        },
        featureClicked: function (feature) {
            var properties = feature.getProperties();
            if (properties['record_type'] === 'site') {
                Shared.Dispatcher.trigger('locationSite-' + properties.id + ':clicked');

                // call geocontext
                var coordinates = feature.getGeometry().getCoordinates();
                coordinates = ol.proj.transform(coordinates, "EPSG:3857", "EPSG:4326");
                this.geocontext.loadGeocontext(coordinates[0], coordinates[1]);

            } else {
                Shared.Dispatcher.trigger('cluster-biology' + properties.id + ':clicked');
            }
            this.layers.highlightVectorSource.clear();
            if (this.layers.layerStyle.isIndividialCluster(feature)) {
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
            self.fetchingRecords();
        },
        loadMap: function () {
            var self = this;
            var mousePositionControl = new ol.control.MousePosition({
                projection: 'EPSG:4326',
                target: document.getElementById('mouse-position-wrapper'),
                coordinateFormat: function (coordinate) {
                    return ol.coordinate.format(coordinate, '{y},{x}', 4);
                }
            });
            var basemap = new Basemap();

            var center = [22.937506, -30.559482];
            if (centerPointMap) {
                var centerArray = centerPointMap.split(',');
                for (var i in centerArray) {
                    centerArray[i] = parseFloat(centerArray[i]);
                }
                center = centerArray;
            }

            this.map = new ol.Map({
                target: 'map',
                layers: basemap.getBaseMaps(),
                view: new ol.View({
                    center: ol.proj.fromLonLat(center),
                    zoom: 7,
                    minZoom: 7,
                    extent: [579700.2488501729, -4540000.22437294, 5275991.266691402, -2101353.2739626765]
                }),
                controls: ol.control.defaults({
                    zoom: false
                }).extend([mousePositionControl])
            });
            this.initExtent = this.getCurrentBbox();

            // Create a popup overlay which will be used to display feature info
            this.popup = new ol.Overlay({
                element: document.getElementById('popup'),
                positioning: 'bottom-center',
                offset: [0, -55]
            });
            this.map.addOverlay(this.popup);
            this.layers.addLayersToMap(this.map);
            this.startOnHoverListener();
        },
        reloadXHR: function () {
            this.previousZoom = -1;
            this.clusterCollection.administrative = null;
            this.fetchingRecords();
            $('#fetching-error .call-administrator').show();
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
            this.layers.biodiversitySource.clear();
        },
        fetchingError: function (err) {
            if (err['textStatus'] !== "abort") {
                $('#fetching-error').show();
                $('#loading-warning').hide();
            }
            this.mapInteractionEnabled = true;
            this.map.getInteractions().forEach(function (interaction) {
                interaction.setActive(true);
            });
        },
        fetchingReset: function () {
            $('#fetching-error').hide();
            $('#loading-warning').hide();
            $('#fetching-error .call-administrator').hide();
            if (this.layers.administrativeBoundarySource) {
                this.layers.administrativeBoundarySource.clear();
            }
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
        fetchingRecords: function () {
            // get records based on administration
            var self = this;
            self.updateClusterBiologicalCollectionZoomExt();
            if (!this.clusterBiologicalCollection.isActive()) {
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
                    this.boundaryView.renderAdministrativeBoundary(
                        administrative, this.getCurrentBbox());

                    // if layer is shows
                    if (!this.layers.isBiodiversityLayerShow()) {
                        return;
                    }

                    this.previousZoom = zoomLevel;
                    this.clusterCollection.updateUrl(administrative);
                    if (this.clusterCollection.getCache()) {
                        this.layers.biodiversitySource.clear();
                        this.clusterCollection.applyCache();
                    } else {
                        this.fetchingStart();
                        this.fetchXhr = this.clusterCollection.fetch({
                            success: function () {
                                self.fetchingFinish();
                                self.clusterCollection.renderCollection()
                            }, error: function (xhr, text_status, error_thrown) {
                                self.fetchingError(error_thrown);
                            }
                        });
                    }
                } else {
                    // if layer is shows
                    if (!this.layers.isBiodiversityLayerShow()) {
                        return;
                    }
                    this.previousZoom = -1;
                    this.clusterCollection.administrative = null;
                    this.fetchingReset();
                    this.fetchingStart();
                    this.locationSiteCollection.updateUrl(
                        this.getCurrentBbox(), this.getCurrentZoom());
                    this.fetchXhr = this.locationSiteCollection.fetch({
                        success: function () {
                            self.fetchingFinish();
                            self.locationSiteCollection.renderCollection()
                        }, error: function (xhr, text_status, error_thrown) {
                            self.fetchingError(error_thrown);
                        }
                    });
                }
            } else {
                // if layer is shows
                if (!this.layers.isBiodiversityLayerShow()) {
                    return;
                }
                this.fetchingReset();
                this.fetchingStart();
                this.fetchXhr = this.clusterBiologicalCollection.fetch({
                    success: function () {
                        self.fetchingFinish();
                        self.clusterBiologicalCollection.renderCollection();
                    }, error: function (xhr, text_status, error_thrown) {
                        self.fetchingError(error_thrown);
                    }
                });
            }
        },
        updateClusterBiologicalCollectionTaxonID: function (taxonID, taxonName) {
            this.closeHighlight();
            if (!this.sidePanelView.isSidePanelOpen()) {
                return
            }
            this.clusterBiologicalCollection.updateTaxon(taxonID, taxonName);
            if (!this.clusterBiologicalCollection.isActive()) {
                this.clusterCollection.administrative = null;
                this.previousZoom = -1;
                this.fetchingRecords();
            } else {
                this.clusterBiologicalCollection.getExtentOfRecords();
            }
        },
        updateClusterBiologicalCollectionZoomExt: function () {
            this.clusterBiologicalCollection.updateZoomAndBBox(
                this.getCurrentZoom(), this.getCurrentBbox());
        },
        addBiodiversityFeatures: function (features) {
            this.layers.biodiversitySource.addFeatures(features);
        },
        addHighlightFeature: function (feature) {
            this.layers.highlightVectorSource.addFeature(feature);
        },
        updateAdministrativeBoundaryFeatures: function (features) {
            this.layers.administrativeBoundarySource.addFeatures(features);
        },
        closeHighlight: function () {
            this.hidePopup();
            this.layers.highlightVectorSource.clear();
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
        }
    })
});
