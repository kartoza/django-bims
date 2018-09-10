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
    'jquery',
    'layerSwitcher',
    'views/olmap_basemap',
    'views/olmap_layers',
    'views/geocontext',
    'views/location_site_detail',
    'views/taxon_detail',
    'views/biodiversity_legend'
], function (Backbone, _, Shared, LocationSiteCollection, ClusterCollection,
             ClusterBiologicalCollection, MapControlPanelView, SidePanelView,
             ol, $, LayerSwitcher, Basemap, Layers, Geocontext,
             LocationSiteDetail, TaxonDetail, BioLegendView) {
    return Backbone.View.extend({
        template: _.template($('#map-template').html()),
        className: 'map-wrapper',
        map: null,
        uploadDataState: false,
        isBoundaryEnabled: false,
        // attributes
        mapInteractionEnabled: true,
        previousZoom: 0,
        sidePanelView: null,
        initZoom: 7,
        initCenter: [22.937506, -30.559482],
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
            this.locationSiteCollection = new LocationSiteCollection();
            this.clusterCollection = new ClusterCollection();
            this.geocontext = new Geocontext();
            new LocationSiteDetail();
            new TaxonDetail();

            Shared.Dispatcher.on('map:addBiodiversityFeatures', this.addBiodiversityFeatures, this);
            Shared.Dispatcher.on('map:zoomToCoordinates', this.zoomToCoordinates, this);
            Shared.Dispatcher.on('map:zoomToExtent', this.zoomToExtent, this);
            Shared.Dispatcher.on('map:reloadXHR', this.reloadXHR, this);
            Shared.Dispatcher.on('map:showPopup', this.showPopup, this);
            Shared.Dispatcher.on('map:closeHighlight', this.closeHighlight, this);
            Shared.Dispatcher.on('map:addHighlightFeature', this.addHighlightFeature, this);
            Shared.Dispatcher.on('map:switchHighlight', this.switchHighlight, this);
            Shared.Dispatcher.on('searchResult:updateTaxon', this.updateClusterBiologicalCollectionTaxonID, this);
            Shared.Dispatcher.on('map:addHighlightPinnedFeature', this.addHighlightPinnedFeature, this);
            Shared.Dispatcher.on('map:switchHighlightPinned', this.switchHighlightPinned, this);
            Shared.Dispatcher.on('map:closeHighlightPinned', this.closeHighlightPinned, this);
            Shared.Dispatcher.on('map:refetchRecords', this.refetchRecords, this);
            Shared.Dispatcher.on('map:zoomToHighlightPinnedFeatures', this.zoomToHighlightPinnedFeatures, this);
            Shared.Dispatcher.on('map:boundaryEnabled', this.boundaryEnabled, this);

            this.render();
            this.clusterBiologicalCollection = new ClusterBiologicalCollection(this.initExtent);
            this.mapControlPanel.searchView.initDateFilter();
            this.showInfoPopup();
        },
        zoomInMap: function (e) {
            var view = this.map.getView();
            var zoom = view.getZoom();
            view.animate({
                zoom: zoom - 1,
                duration: 250
            })
        },
        boundaryEnabled: function (value) {
            this.isBoundaryEnabled = value;
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
            this.previousZoom = this.getCurrentZoom();
            this.map.getView().setCenter(coordinates);
            if (typeof zoomLevel !== 'undefined') {
                this.map.getView().setZoom(zoomLevel);
            }
        },
        zoomToExtent: function (coordinates) {
            if (this.isBoundaryEnabled) {
                this.fetchingRecords();
                return false;
            }
            this.previousZoom = this.getCurrentZoom();
            var ext = ol.proj.transformExtent(coordinates, ol.proj.get('EPSG:4326'), ol.proj.get('EPSG:3857'));
            this.map.getView().fit(ext, {
                size: this.map.getSize(), padding: [
                    0, $('.right-panel').width(), 0, 250
                ]
            });
            this.map.getView().setZoom(this.getCurrentZoom());
            if (this.getCurrentZoom() > 18) {
                this.map.getView().setZoom(18);
            }
        },
        mapClicked: function (e) {
            var self = this;
            var features = self.map.getFeaturesAtPixel(e.pixel);
            this.layers.highlightVectorSource.clear();
            this.hidePopup();

            // Point of interest flag
            var featuresClickedResponseData = [];
            var poiFound = false;
            var featuresData = '';

            if (features) {
                var geometry = features[0].getGeometry();
                var geometryType = geometry.getType();

                if (geometryType === 'Point') {
                    featuresClickedResponseData = self.featureClicked(features[0], self.uploadDataState);
                    poiFound = featuresClickedResponseData[0];
                    featuresData = featuresClickedResponseData[1];

                    var coordinates = geometry.getCoordinates();
                    self.zoomToCoordinates(coordinates);
                    // increase zoom level if it is clusters
                    if (features[0].getProperties()['count'] &&
                        features[0].getProperties()['count'] > 1) {
                        self.map.getView().setZoom(self.getCurrentZoom() + 1);
                        poiFound = true;
                    }
                }
            }

            if (self.uploadDataState && !poiFound) {
                // Get lat and long map
                var lonlat = ol.proj.transform(e.coordinate, 'EPSG:3857', 'EPSG:4326');
                var lon = lonlat[0];
                var lat = lonlat[1];
                self.mapControlPanel.showUploadDataModal(lon, lat, featuresData);
            }

            // Close opened control panel
            this.mapControlPanel.closeSearchPanel();

        },
        featureClicked: function (feature, uploadDataState) {
            var properties = feature.getProperties();
            if (!properties.hasOwnProperty('record_type')) {
                return [false, ''];
            }

            if (uploadDataState) {
                return [false, feature];
            }

            if (properties['record_type'] === 'site') {
                Shared.Dispatcher.trigger('locationSite-' + properties.id + ':clicked');

                // Load geocontext value for the ID
                this.geocontext.loadGeocontextByID(properties['id']);

            } else {
                Shared.Dispatcher.trigger('cluster-biology' + properties.id + ':clicked');
            }
            this.layers.highlightVectorSource.clear();
            if (this.layers.layerStyle.isIndividialCluster(feature)) {
                this.addHighlightFeature(feature);
            }
            return [true, properties];
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

            this.bioLegendView = new BioLegendView();
            this.$el.append(this.bioLegendView.render().$el);

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

            var center = this.initCenter;
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
                    zoom: this.initZoom,
                    minZoom: 5,
                    extent: [579700.2488501729, -4540000.22437294, 5275991.266691402, -2101353.2739626765]
                }),
                controls: ol.control.defaults({
                    zoom: false
                }).extend([mousePositionControl])
            });

            // Create a popup overlay which will be used to display feature info
            this.popup = new ol.Overlay({
                element: document.getElementById('popup'),
                positioning: 'bottom-center',
                offset: [0, -55]
            });
            this.map.addOverlay(this.popup);
            this.layers.addLayersToMap(this.map);
            this.startOnHoverListener();
            this.initExtent = this.getCurrentBbox();
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
            if(!this.layers.isBiodiversityLayerLoaded()) {
                return
            }
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
                    this.layers.changeLayerAdministrative(administrative);

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
            if (!this.sidePanelView.isSidePanelOpen() && !this.mapControlPanel.searchView.searchPanel.isPanelOpen()) {
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
        switchHighlight: function (features, ignoreZoom) {
            var self = this;
            this.closeHighlight();
            $.each(features, function (index, feature) {
                self.addHighlightFeature(feature);
            });
            if (!ignoreZoom) {
                var extent = this.layers.highlightVectorSource.getExtent();
                this.map.getView().fit(extent, {
                    size: this.map.getSize(), padding: [
                        0, $('.right-panel').width(), 0, 250
                    ]
                });
                if (this.getCurrentZoom() > 18) {
                    this.map.getView().setZoom(18);
                }
            }
        },
        addHighlightFeature: function (feature) {
            this.layers.highlightVectorSource.addFeature(feature);
        },
        closeHighlight: function () {
            this.hidePopup();
            if (this.layers.highlightVectorSource) {
                this.layers.highlightVectorSource.clear();
            }
        },
        switchHighlightPinned: function (features, ignoreZoom) {
            var self = this;
            this.closeHighlightPinned();
            $.each(features, function (index, feature) {
                self.addHighlightPinnedFeature(feature);
            });
        },
        zoomToHighlightPinnedFeatures: function () {
            this.map.getView().fit(
                this.layers.highlightPinnedVectorSource.getExtent(),
                {
                    size: this.map.getSize(),
                    padding: [
                        0, $('.right-panel').width(), 0, 250
                    ]
                });
        },
        addHighlightPinnedFeature: function (feature) {
            this.layers.highlightPinnedVectorSource.addFeature(feature);
        },
        closeHighlightPinned: function () {
            this.hidePopup();
            if (this.layers.highlightPinnedVectorSource) {
                this.layers.highlightPinnedVectorSource.clear();
            }
        },
        startOnHoverListener: function () {
            var that = this;
            this.pointerMoveListener = this.map.on('pointermove', function (e) {
                var pixel = that.map.getEventPixel(e.originalEvent);
                var hit = that.map.hasFeatureAtPixel(pixel);
                if (that.uploadDataState) {
                    $('#' + that.map.getTarget()).find('canvas').css('cursor', 'pointer');
                } else if (hit) {
                    that.map.forEachFeatureAtPixel(pixel,
                        function (feature, layer) {
                            if (feature.getGeometry().getType() == 'Point') {
                                $('#' + that.map.getTarget()).find('canvas').css('cursor', 'pointer');
                            }
                        })
                } else {
                    $('#' + that.map.getTarget()).find('canvas').css('cursor', 'move');
                }
            });
        },
        showInfoPopup: function () {
            if(!hideBimsInfo && bimsInfoContent) {
                $('#general-info-modal').fadeIn()
            }
        },
        refetchRecords: function () {
            var center = this.initCenter;
            if (centerPointMap) {
                var centerArray = centerPointMap.split(',');
                for (var i in centerArray) {
                    centerArray[i] = parseFloat(centerArray[i]);
                }
                center = centerArray;
            }
            this.zoomToCoordinates(ol.proj.fromLonLat(center), this.initZoom);
            this.fetchingRecords();
        }
    })
});
