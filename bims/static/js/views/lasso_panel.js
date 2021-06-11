define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery', 'ol'], function (Shared, Backbone, _, jqueryUi, $, ol) {
    return Backbone.View.extend({
        template: _.template($('#lasso-control-panel-template').html()),
        isEmpty: true,
        layer: null,
        source: null,
        polygonDraw: null,
        polygonCoordinates: null,
        searchResultCollection: null,
        displayed: false,
        polygonExist: false,
        maxSites: 10,
        minSites: 2,
        events: {
            'click .polygonal-lasso-tool': 'drawPolygon',
            'click .clear-lasso': 'clearLasso',
            'click .update-search': 'updateSearch',
            'click .merge-sites': 'mergeSitesModal',
            'click #merge-site-btn': 'mergeSites'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.map = options.map;
            this.createPolygonInteraction();
            Shared.Dispatcher.on('search:finished', this.toggleMergeSites, this);
        },
        createPolygonInteraction: function () {
            let self = this;
            this.source = new ol.source.Vector({wrapX: false});
            this.layer = new ol.layer.Vector({
                source: self.source
            });
            this.polygonDraw = new ol.interaction.Draw({
                source: self.source,
                type: 'Polygon'
            });
            this.polygonDraw.on('drawend', function (evt) {
                // Zoom to extent
                let polygonExtent = evt.feature.getGeometry().getExtent();
                let transformedCoordinates = [];
                let coordinates = evt.feature.getGeometry().getCoordinates()[0];
                for (let i=0; i<coordinates.length; i++) {
                    let newCoord = ol.proj.transform(coordinates[i], ol.proj.get('EPSG:3857'), ol.proj.get('EPSG:4326'));
                    transformedCoordinates.push(newCoord);
                }
                self.polygonCoordinates = transformedCoordinates;
                self.polygonExist = true;
                self.$el.find('.update-search').removeClass('disabled');
                self.$el.find('.clear-lasso').removeClass('disabled');
                Shared.Dispatcher.trigger('map:zoomToExtent', polygonExtent, false, false);
                Shared.Dispatcher.trigger('map:setPolygonDrawn', polygonExtent);
            });
            this.polygonDraw.on('drawstart', function () {
                self.source.clear();
            });
        },
        render: function () {
            this.$el.html(this.template());
            this.$el.hide();
            if (isSuperUser) {
                this.$el.find('.merge-sites').show();
            }
            return this;
        },
        getPolygonCoordinates: function () {
            if (this.polygonCoordinates) {
                return JSON.stringify(this.polygonCoordinates);
            }
            return '';
        },
        show: function () {
            this.$el.show();
            this.$el.find('.lasso-control-container').show();
            if (this.polygonExist) {
                this.$el.find('.update-search').removeClass('disabled');
                this.$el.find('.clear-lasso').removeClass('disabled');
            } else {
                if (!Shared.CurrentState.SEARCH) {
                    this.$el.find('.update-search').addClass('disabled');
                }
                this.$el.find('.clear-lasso').addClass('disabled');
            }
            this.displayed = true;
        },
        hide: function () {
            this.$el.hide();
            this.$el.find('.lasso-control-container').hide();
            this.stopDrawing();
            this.displayed = false;
        },
        isDisplayed: function () {
            return this.displayed;
        },
        drawPolygon: function () {
            this.$el.find('.polygonal-lasso-tool').addClass('selected');
            this.map.removeLayer(this.layer);
            this.map.addLayer(this.layer);
            this.map.addInteraction(this.polygonDraw);
            Shared.Dispatcher.trigger('map:toggleMapInteraction', true);
        },
        stopDrawing: function () {
            this.$el.find('.polygonal-lasso-tool').removeClass('selected');
            this.map.removeInteraction(this.polygonDraw);
            Shared.Dispatcher.trigger('map:toggleMapInteraction', false);
        },
        clearLasso: function (evt) {
            if (evt) {
                let div = $(evt.target);
                if (div.hasClass('disabled')) {
                    return;
                }
            }
            this.map.removeLayer(this.layer);
            this.source.clear();
            this.polygonCoordinates = null;
            this.polygonExist = false;
            if (!Shared.CurrentState.SEARCH) {
                this.$el.find('.update-search').addClass('disabled');
            }
            this.$el.find('.clear-lasso').addClass('disabled');
            this.stopDrawing();
            Shared.Dispatcher.trigger('map:setPolygonDrawn', null);
        },
        drawPolygonFromJSON: function (jsonCoordinates) {
            if (this.polygonExist) {
                return;
            }
            this.polygonCoordinates = JSON.parse(jsonCoordinates);
            let polyCoords = [];
            for (let i in this.polygonCoordinates) {
                let c = this.polygonCoordinates[i];
                polyCoords.push(ol.proj.transform(c, 'EPSG:4326', 'EPSG:3857'));
            }
            const feature = new ol.Feature({
                geometry: new ol.geom.Polygon([polyCoords])
            });
            this.map.removeLayer(this.layer);
            this.map.addLayer(this.layer);
            this.source.addFeature(feature);
            this.polygonExist = true;
        },
        updateSearch: function (evt) {
            let div = $(evt.target);
            if (div.hasClass('disabled')) {
                return;
            }
            Shared.Dispatcher.trigger('search:doSearch');
        },
        toggleMergeSites: function (status) {
            if (this.polygonExist && status && this.searchResultCollection.sitesData.length <= this.maxSites && this.searchResultCollection.sitesData.length >= this.minSites) {
                this.$el.find('.merge-sites').removeClass('disabled');
                return true;
            }
            this.$el.find('.merge-sites').addClass('disabled');
        },
        mergeSitesModal: function (evt) {
            const $modal = this.$el.find('#merge-sites-modal');
            const $sitesOptionContainer = $modal.find('#sites-selection');
            $sitesOptionContainer.html('');
            $.each(this.searchResultCollection.sitesData, function(index, value) {
                $sitesOptionContainer.append(`<option value=${value['site_id']}>${value['name']}</option>`);
            });
            $modal.modal('show');
        },
        mergeSites: function (evt) {
            if ($(evt.target).hasClass('disabled')) return false;
            const $modal = this.$el.find('#merge-sites-modal');
            const $selectedSite = $("#sites-selection option:selected")
            const selectedPrimarySite = $selectedSite.val();
            const selectedSiteLabel = $selectedSite.html();
            const secondarySites = this.searchResultCollection.sitesData.filter(
                function (data) {
                    return '' + data['site_id'] !== selectedPrimarySite
                }
            ).map(function(data) {
                return data['site_id'];
            })
            const putData = {
                'primary_site': selectedPrimarySite,
                'merged_sites': secondarySites.join(','),
                'query_url': window.location.href
            }
            let r = confirm(`Are you sure you want to merge the sites to ${selectedSiteLabel}?`);
            if (r) {
                // Show loading...
                $('#merge-site-btn').addClass("disabled").html(
                    '<img src="/static/img/small-loading.svg" width="20" style="filter: brightness(104%) contrast(97%);" alt="Loading view">'
                )
                $.ajax({
                    url: '/api/merge-sites/',
                    type: 'PUT',
                    data: putData,
                    headers: {"X-CSRFToken": csrfmiddlewaretoken},
                    success: function (result) {
                        // Do something with the result
                        $('#merge-site-btn').removeClass("disabled").html('Merge')
                        $modal.modal('hide');
                        Shared.Dispatcher.trigger('search:doSearch');
                    },
                    error: function (e) {
                        alert(e.responseText);
                        $('#merge-site-btn').removeClass("disabled").html('Merge')
                    }
                });
            }

        }
    })
});
