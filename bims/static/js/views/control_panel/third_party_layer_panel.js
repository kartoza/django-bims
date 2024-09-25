define(['shared', 'backbone', 'underscore', 'jqueryUi',
    'jquery'], function (Shared, Backbone, _, jqueryUi, $) {
    return Backbone.View.extend({
        template: _.template($('#third-party-layer-panel-template').html()),
        isEmpty: true,
        layer: null,
        source: null,
        displayed: false,
        miniSASSSelected: false,
        inWARDSelected: false,
        fetchingInWARDSData: false,
        fetchingMiniSASS: false,
        inWARDSStationsUrl: "/bims_proxy/https://inwards.award.org.za/app_json/wq_stations.php",
        miniSASSUrl: "/api/minisass-observations/",
        events: {
            'click .close-button': 'closeClicked',
            'click .update-search': 'updateSearch',
            'change .mini-sass-check': 'toggleMiniSASSLayer',
            'change .inward-check': 'toggleInward'
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.map = options.map;
            this.addMiniSASSLayer();
            this.addInWARDSLayer();
            Shared.Dispatcher.on('third_party_layers:showFeatureInfo', this.showFeatureInfo, this);
        },
        inWARDSStyleFunction: function (feature) {
            let properties = feature.getProperties();
            let color = 'gray';
            if (properties['color']) {
                color = properties['color'];
            } else {
                color = '#C6401D';
            }
            let image = new ol.style.Circle({
                radius: 5,
                fill: new ol.style.Fill({color: color})
            });
            return new ol.style.Style({
                image: image
            });
        },
        miniSASSStyleFunction: function (feature) {
            let properties = feature.getProperties();
            let color = 'gray';
            if (properties['color']) {
                color = properties['color'];
            } else {
                color = '#1dc6c0';
            }
            let image = new ol.style.Circle({
                radius: 5,
                fill: new ol.style.Fill({color: color})
            });
            return new ol.style.Style({
                image: image
            });
        },
        addInWARDSLayer: function () {
            this.inWARDSLayer = new ol.layer.Vector({
                source: null,
                style: this.inWARDSStyleFunction
            });
            this.inWARDSLayer.setVisible(false);
            this.map.addLayer(this.inWARDSLayer);
        },
        addMiniSASSLayer: function () {
            this.miniSASSLayer = new ol.layer.Vector({
                source: null,
                style: this.miniSASSStyleFunction
            });
            this.miniSASSLayer.setVisible(false);
            this.map.addLayer(this.miniSASSLayer);
        },
        isValidCoordinate: function(coordinate) {
          const [longitude, latitude] = coordinate;
          if (
            typeof longitude !== 'number' ||
            typeof latitude !== 'number' ||
            longitude < -180 ||
            longitude > 180 ||
            latitude < -90 ||
            latitude > 90
          ) {
            return false;
          }
          return true;
        },
        toggleMiniSASSLayer: function (e) {
            let self = this;
            this.miniSASSSelected = $(e.target).is(":checked");
            if (this.miniSASSSelected) {
                this.miniSASSLayer.setVisible(true);
                // Move layer to top
                this.map.removeLayer(this.miniSASSLayer);
                this.map.getLayers().insertAt(this.map.getLayers().getLength(), this.miniSASSLayer);

                // Show fetching message
                if (!this.fetchingMiniSASS) {
                    let fetchingMessage = $('<span class="fetching" style="font-size: 10pt; font-style: italic"> (fetching)</span>');
                    $(e.target).parent().find('.label').append(fetchingMessage);

                    $.ajax({
                        type: 'GET',
                        url: this.miniSASSUrl,
                        success: function (data) {
                            let geojson = {
                                "type": "FeatureCollection",
                                "features": []
                            }
                            for(let i=0; i < data.length; i++) {
                                let observation = data[i];
                                let coordinate = [parseFloat(observation.longitude), parseFloat(observation.latitude)];
                                if (self.isValidCoordinate(coordinate)) {
                                    let properties = observation;
                                    delete properties.longitude;
                                    delete properties.latitude;
                                    let feature = {
                                        "type": "Feature",
                                        "geometry": {"type": "Point", "coordinates": coordinate},
                                        "properties": properties
                                    }
                                    geojson.features.push(feature);
                                }
                            }
                            let source = new ol.source.Vector({
                                features: (
                                    new ol.format.GeoJSON()
                                ).readFeatures(geojson, {featureProjection: 'EPSG:3857'})
                            });
                            self.miniSASSLayer.setSource(source);
                            $(e.target).parent().find('.fetching').remove();
                        }
                    })
                    this.fetchingMiniSASS = true;
                }
            } else {
                this.miniSASSLayer.setVisible(false);
            }
        },
        toggleInward: function (e) {
            let self = this;
            this.inWARDSelected = $(e.target).is(":checked");

            if (this.inWARDSelected) {
                this.inWARDSLayer.setVisible(true);
                // Move layer to top
                this.map.removeLayer(this.inWARDSLayer);
                this.map.getLayers().insertAt(this.map.getLayers().getLength(), this.inWARDSLayer);

                // Show fetching message
                if (!this.fetchingInWARDSData) {
                    let fetchingMessage = $('<span class="fetching" style="font-size: 10pt; font-style: italic"> (fetching)</span>');
                    $(e.target).parent().find('.label').append(fetchingMessage);
                    $.ajax({
                        type: 'GET',
                        url: this.inWARDSStationsUrl,
                        success: function (data) {
                            const regex = /"id":null,/gi;
                            const updatedData = JSON.parse(JSON.stringify(data).replaceAll(regex, ''));
                            let source = new ol.source.Vector({
                                features: (
                                    new ol.format.GeoJSON({featureProjection: 'EPSG:3857'})
                                ).readFeatures(updatedData, {featureProjection: 'EPSG:3857'})
                            });
                            self.inWARDSLayer.setSource(source);
                            $(e.target).parent().find('.fetching').remove();
                        }
                    })
                    this.fetchingInWARDSData = true;
                }
            } else {
                self.inWARDSLayer.setVisible(false);
            }
        },
        objectToTable: function (obj) {
            // Create the table and the table body
            let table = document.createElement('table');
            let tbody = document.createElement('tbody');

            function handleValue(value) {
                if (value && typeof value === 'object') {
                    try {
                        // Attempt to convert the object to a string
                        return JSON.stringify(value, getCircularReplacer(), 2);
                    } catch (error) {
                        // Fallback for objects that cannot be stringified
                        return '[Circular]';
                    }
                } else {
                    return value !== null ? value : 'null';
                }
            }

            function getCircularReplacer() {
                const seen = new WeakSet();
                return (key, value) => {
                    if (typeof value === "object" && value !== null) {
                        if (seen.has(value)) {
                            return "[Circular]";
                        }
                        seen.add(value);
                    }
                    return value;
                };
            }

            for (let key in obj) {
                if (obj.hasOwnProperty(key)) {
                    let tr = document.createElement('tr');

                    let tdKey = document.createElement('td');
                    tdKey.textContent = key;
                    tr.appendChild(tdKey);

                    let tdValue = document.createElement('td');
                    tdValue.textContent = handleValue(obj[key]);
                    tr.appendChild(tdValue);

                    tbody.appendChild(tr);
                }
            }

            table.appendChild(tbody);

            table.style.borderCollapse = 'collapse';
            table.style.width = '100%';
            table.style.margin = '20px 0';

            let cells = table.querySelectorAll('td');
            cells.forEach(cell => {
                cell.style.border = '1px solid #ddd';
                cell.style.padding = '8px';
            });

            return table;
        },
        showFeatureInfo: function (lon, lat, siteExist = false, featureData = null) {
            if (!this.miniSASSSelected && !this.inWARDSelected) {
                return false;
            }
            let self = this;
            lon = parseFloat(lon);
            lat = parseFloat(lat);
            const view = this.map.getView();
            const coordinate = ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857');
            let openSidePanel = false;

            if (this.inWARDSelected) {
                if (!featureData) {
                    return;
                }
                let properties = featureData.getProperties();
                let stationName = 'Station';
                if (properties.hasOwnProperty('station')) {
                    stationName = 'Station - ' + properties['station'];
                }
                let table = this.renderInwardsTable(properties);
                this.showContentToSidePanel(
                    lon, lat, stationName, table.prop('outerHTML'), siteExist, openSidePanel
                )
                openSidePanel = true;
            }

            if (this.miniSASSSelected) {
                const source = this.miniSASSLayer.getSource();
                const pixel = this.map.getPixelFromCoordinate(coordinate);
                let minisassData = [];
                self.map.forEachFeatureAtPixel(pixel, function(feature) {
                    if (feature.getProperties().hasOwnProperty('minisass_ml_score')) {
                        minisassData.push(feature.getProperties())
                    }
                    if (minisassData.length > 0) {
                        let minisassDataTable = minisassData[0];
                        delete minisassDataTable['geometry'];
                        delete minisassDataTable['organisationtype'];
                        delete minisassDataTable['images'];
                        delete minisassDataTable['site'];
                        const minisassTable = $(self.objectToTable(minisassDataTable));
                        self.showContentToSidePanel(
                            lon, lat, minisassData[0]['sitename'], minisassTable.prop('outerHTML'), siteExist, openSidePanel
                        )
                    }
                });

            }
        },
        showContentToSidePanel: function (lon, lat, panelTitle, panelContent, siteExist, openSidePanel = false) {
            if (!siteExist && !openSidePanel) {
                let marker = new ol.Feature({
                    geometry: new ol.geom.Point(
                        ol.proj.fromLonLat([lon, lat])
                    ),
                });
                Shared.Dispatcher.trigger('sidePanel:openSidePanel', {});
                Shared.Dispatcher.trigger('map:switchHighlight', [marker], true);
            }
            Shared.Dispatcher.trigger('sidePanel:addContentWithTab', panelTitle, panelContent);
        },
        renderInwardsTable: function (properties) {
            let $container = $(`<div></div>`);
            let table = $(`<table class="table table-striped"></table>`);
            $container.append(table);
            for (let key in properties) {
                if (properties[key] !== null && properties[key].constructor !== String && properties[key].constructor !== Number) {
                    continue;
                }
                let title = key;
                title = title.replace(/_/g, ' ');
                table.append(`<tr><td style="text-transform: capitalize; min-width: 100px;">${title}</td><td>${properties[key]}</td></tr>`);
            }
            let id = '';
            if (properties.hasOwnProperty('station')) {
                id = properties['station'];
            }
            $container.append(`<button class="btn btn-default" style="width: 100%" onclick="window.open('http://inwards.award.org.za/app_json/wq_csv.php?id=${id}')">Download csv</button>`);
            $container.append('<div style="text-align: right; font-size: 11pt">Data shared with permission from <a target="_blank" href="http://award.org.za/">http://award.org.za/</a></div>');
            return $container;
        },
        render: function () {
            this.$el.html(this.template());
            this.$el.hide();
            return this;
        },
        show: function () {
            this.$el.show();
            this.$el.find('.third-party-control-container').show();
            this.displayed = true;
        },
        hide: function () {
            this.$el.hide();
            this.$el.find('.third-party-control-container').hide();
            this.displayed = false;
        },
        isDisplayed: function () {
            return this.displayed;
        },
        closeClicked: function () {
            if (this.displayed) {
                Shared.Dispatcher.trigger('mapControlPanel:thirdPartyLayerClicked');
            }
        }
    })
});
