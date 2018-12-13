define(['backbone', 'ol', 'shared', 'underscore', 'jquery', 'chartJs', 'fileSaver', 'htmlToCanvas'], function (
    Backbone,
    ol,
    Shared,
    _,
    $,
    ChartJs,
    FileSaver,
    Html2Canvas
) {
    return Backbone.View.extend({
        id: 'detailed-taxa-dashboard',
        template: _.template($('#taxon-detail-dashboard-template').html()),
        objectDataByYear: 'object_data_by_year',
        yearsArray: 'years_array',
        isOpen: false,
        events: {
            'click .close-dashboard': 'closeDashboard',
            'click #export-taxasite-map': 'exportTaxasiteMap',
            'click .download-taxa-records-timeline': 'downloadTaxaRecordsTimeline'
        },
        apiParameters: _.template(Shared.SearchURLParametersTemplate),
        initialize: function () {
            this.$el.hide();
        },
        render: function () {
            this.$el.html(this.template());
            this.loadingDashboard = this.$el.find('.loading-dashboard');
            this.dashboardTitleContainer = this.$el.find('.detailed-dashboard-title');
            this.originInfoList = this.$el.find('.origin-info-list');
            this.endemicInfoList = this.$el.find('.endemic-info-list');
            this.conservationStatusList = this.$el.find('.conservation-status-list');
            this.overviewTaxaTable = this.$el.find('.overview-taxa-table');
            this.overviewNameTaxonTable = this.$el.find('.overview-name-taxonomy-table');
            this.taxaRecordsTimelineGraph = this.$el.find('#taxa-records-timeline-graph');
            this.taxaRecordsTimelineGraphChart = null;
            this.taxaRecordsTimelineGraphCanvas = this.taxaRecordsTimelineGraph[0].getContext('2d');
            this.recordsTable = this.$el.find('.records-table');
            this.recordsAreaTable = this.$el.find('.records-area-table');
            this.siteGeoPoints = {};
            this.mapTaxaSite = null;
            this.taxaVectorLayer = null;
            this.taxaVectorSource = null;
            return this;
        },
        show: function (data) {
            if(this.isOpen) {
                return false;
            }
            this.isOpen = true;
            this.loadingDashboard.show();
            this.taxonName = data.taxonName;
            this.taxonId = data.taxonId;
            this.siteDetail = data.siteDetail;
            if (typeof filterParameters !== 'undefined') {
                this.parameters = filterParameters;
                this.parameters['taxon'] = this.taxonId;
            }
            this.url = '/api/get-bio-records/' + this.apiParameters(this.parameters);
            this.fetchRecords();
            this.$el.show('slide', {
                direction: 'right'
            }, 300, function () {
            });
        },
        fetchRecords: function () {
            var self = this;
            $.get({
                url: this.url,
                dataType: 'json',
                success: function (data) {
                    self.generateDashboard(data);
                    self.loadingDashboard.hide();
                }
            })
        },
        generateTaxonDetailDashboard: function (taxonomy_id) {
            var self = this;
            $.get({
                url: '/api/taxon/' + taxonomy_id,
                dataType: 'json',
                success: function (data) {
                    var taxonomySystem = self.$el.find('.taxon-dashboard-detail');
                    if (data.hasOwnProperty('kingdom')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>Kingdom</td>' +
                            '<td>' + data['kingdom'] + '</td>' +
                            '</tr>'
                        )
                    }
                    if (data.hasOwnProperty('phylum')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>Phylum</td>' +
                            '<td>' + data['phylum'] + '</td>' +
                            '</tr>'
                        )
                    }
                    if (data.hasOwnProperty('class')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>Class</td>' +
                            '<td>' + data['class'] + '</td>' +
                            '</tr>'
                        )
                    }
                    if (data.hasOwnProperty('order')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>Order</td>' +
                            '<td>' + data['order'] + '</td>' +
                            '</tr>'
                        )
                    }
                    if (data.hasOwnProperty('family')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>Family</td>' +
                            '<td>' + data['family'] + '</td>' +
                            '</tr>'
                        )
                    }
                    if (data.hasOwnProperty('genus')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>genus</td>' +
                            '<td>' + data['genus'] + '</td>' +
                            '</tr>'
                        )
                    }
                    if (data.hasOwnProperty('species')) {
                        taxonomySystem.append(
                            '<tr>' +
                            '<td>Species</td>' +
                            '<td>' + data['species'] + '</td>' +
                            '</tr>'
                        )
                    }

                }
            })
        },
        generateDashboard: function (data) {
            var self = this;
            this.dashboardTitleContainer.html(this.taxonName);
            var gbif_key = data[0]['taxonomy']['gbif_key'];
            var taxonomy_id = data[0]['taxonomy']['id'];

            // Set origin
            var category = data[0]['category'];
            $.each(self.originInfoList.children(), function (key, data) {
                var $originInfoItem = $(data);
                if ($originInfoItem.data('value') === category) {
                    $originInfoItem.css('background-color', 'rgba(5, 255, 103, 0.28)');
                }
            });

            // Set endemic
            var endemic = data[0]['endemism'];
            $.each(this.endemicInfoList.children(), function (key, data) {
                var $endemicInfoItem = $(data);
                if (!endemic) {
                    return true;
                }
                if ($endemicInfoItem.data('value') === endemic.toLowerCase()) {
                    $endemicInfoItem.css('background-color', 'rgba(5, 255, 103, 0.28)');
                }
            });

            // Set con status
            var conservation = data[0]['taxonomy']['iucn_status_name'];
            $.each(this.conservationStatusList.children(), function (key, data) {
                var $conservationStatusItem = $(data);
                if ($conservationStatusItem.data('value') === conservation) {
                    $conservationStatusItem.css('background-color', 'rgba(5, 255, 103, 0.28)');
                }
            });

            var overViewTable = _.template($('#taxon-overview-table').html());
            this.overviewTaxaTable.html(overViewTable({
                id: self.apiParameters(self.parameters),
                count: data.length,
                taxon_class: data[0]['taxonomy']['scientific_name'],
                gbif_id: gbif_key
            }));

            var taxonDetailTable = _.template($('#taxon-detail-table').html());

            this.overviewNameTaxonTable.html(taxonDetailTable(data[0]['taxonomy']));

            var objectPerDate = self.countObjectPerDateCollection(data);
            var dataBySite = self.countObjectPerSite(data);
            var recordsOptions = {
                maintainAspectRatio: false,
                title: {display: true, text: 'Records'},
                legend: {display: false},
                scales: {
                    xAxes: [{
                        barPercentage: 0.4,
                        ticks: {autoSkip: false, maxRotation: 90, minRotation: 90},
                        scaleLabel: {display: true, labelString: 'Year'}
                    }],
                    yAxes: [{
                        stacked: true,
                        scaleLabel: {display: true, labelString: 'Occurrence'}
                    }]
                }
            };

            var objectDatasets= [{
                data: Object.values(objectPerDate[self.objectDataByYear]),
                backgroundColor: 'rgba(222, 210, 65, 1)'
            }];

            this.taxaRecordsTimelineGraphChart = self.createTimelineGraph(
                self.taxaRecordsTimelineGraphCanvas,
                objectPerDate[self.yearsArray],
                objectDatasets,
                recordsOptions);

            var $table = $('<table class="table"></table>');
            for(var key in objectPerDate[self.objectDataByYear]){
                $table.append('<tr><td>' + key + '</td><td>' + objectPerDate[self.objectDataByYear][key] + '</td></tr>')
            }
            self.recordsTable.html($table);

            var $tableArea = $('<table class="table"></table>');
            $tableArea.append('<tr><th>ID</th><th>Site name</th><th>Records</th></tr>')
            for(var site in dataBySite){
                if(dataBySite[site]['site_name'] !== undefined) {
                    $tableArea.append('<tr><td>' + site + '</td><td data-site-id="' + site + '">' + dataBySite[site]['site_name'] + '</td><td>' + dataBySite[site]['count'] + '</td></tr>')
                }else {
                    $tableArea.append('<tr><td>' + site + '</td><td data-site-id="'+site+'">' + site + '</td><td>' + dataBySite[site]['count'] + '</td></tr>')
                }
            }
            if (!this.mapTaxaSite) {
                this.mapTaxaSite = new ol.Map({
                    layers: [
                        new ol.layer.Tile({
                            source: new ol.source.OSM()
                        })
                    ],
                    target: 'taxasite-map',
                    view: new ol.View({
                        center: [0, 0],
                        zoom: 12
                    })
                });
            }
            self.recordsAreaTable.html($tableArea);

            $.each(data, function (index, value) {
                var sites = Object.keys(self.siteGeoPoints);
                if(!sites.includes(value['site'])) {
                    var center = JSON.parse(value['location']);
                    self.siteGeoPoints[value['site']] = center['coordinates'];
                    self.addFeatures(self.siteGeoPoints);
                }
            });

            this.generateTaxonDetailDashboard(taxonomy_id);
        },
        countObjectPerDateCollection: function(data) {
            var yearArray = [];
            var dataByYear = {};
            $.each(data, function (key, value) {
                var collection_year = new Date(value['collection_date']).getFullYear();
                if($.inArray(collection_year, yearArray) === -1){
                    yearArray.push(collection_year)
                }
            });
            yearArray.sort();

            $.each(yearArray, function (idx, year) {
                dataByYear[year] = 0;
                $.each(data, function (key, value) {
                    var valueYear = new Date(value['collection_date']).getFullYear();
                    if(valueYear === year){
                        dataByYear[year] += 1;
                    }
                })
            });

            var self = this;
            var results = {};
            results[self.objectDataByYear] = dataByYear;
            results[self.yearsArray] = yearArray;

            return results;
        },
        countObjectPerSite: function(data) {
            var dataBySite = {};
            $.each(data, function (key, value) {
                if (!dataBySite.hasOwnProperty(value['site'])) {
                    dataBySite[value['site']] = {
                        'count': 1,
                        'site_name': value['site_name']
                    }
                } else {
                    dataBySite[value['site']]['count'] += 1;
                }
            });
            return dataBySite
        },
        clearDashboard: function () {
            $.each(this.originInfoList.children(), function (key, data) {
                var $originInfoItem = $(data);
                $originInfoItem.css('background-color', '');
            });
            $.each(this.conservationStatusList.children(), function (key, data) {
                var $conservationStatusItem = $(data);
                $conservationStatusItem.css('background-color', '');
            });
            $.each(this.endemicInfoList.children(), function (key, data) {
                var $endemicInfoItem = $(data);
                $endemicInfoItem.css('background-color', '');
            });
            this.overviewTaxaTable.html('');
            this.overviewNameTaxonTable.html('');

            // Clear canvas
            if(this.taxaRecordsTimelineGraphChart) {
                this.taxaRecordsTimelineGraphChart.destroy();
                this.taxaRecordsTimelineGraphChart = null;
            }

            this.recordsTable.html('');
            this.recordsAreaTable.html('');
            this.siteGeoPoints = {};

            this.taxaVectorSource.clear();
        },
        closeDashboard: function () {
            var self = this;
            if (!this.isOpen) {
                return false;
            }
            this.$el.hide('slide', {
                direction: 'right'
            }, 300, function () {
                self.isOpen = false;
                self.clearDashboard();
                self.loadingDashboard.hide();
                self.dashboardTitleContainer.html('&nbsp;');
            });
        },
        createTimelineGraph: function(canvas, labels, dataset, options) {
            var chart = new ChartJs(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: dataset
                },
                options: options
            });
            return chart;
        },
        addFeatures: function(data) {
            if(this.taxaVectorLayer){
                this.mapTaxaSite.removeLayer(this.taxaVectorLayer);
                this.taxaVectorLayer = null;
            }

            var iconFeatures=[];

            $.each(data, function (index, value) {
                var center = ol.proj.transform([value[0], value[1]], 'EPSG:4326', 'EPSG:3857');
                var iconFeature = new ol.Feature({
                    geometry: new ol.geom.Point(center)
                });

                var iconStyle = new ol.style.Style({
                    image: new ol.style.Icon(({
                        anchor: [0.5, 46],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        opacity: 0.75,
                        src: '/static/img/map-marker.png'
                    }))
                });
                iconFeature.setStyle(iconStyle);
                iconFeatures.push(iconFeature);
            });

            this.taxaVectorSource = new ol.source.Vector({
                features: iconFeatures
            });

            this.taxaVectorLayer = new ol.layer.Vector({
                source: this.taxaVectorSource
            });
            this.mapTaxaSite.addLayer(this.taxaVectorLayer);
            this.mapTaxaSite.getView().fit(this.taxaVectorLayer.getSource().getExtent(), this.mapTaxaSite.getSize());
        },
        exportTaxasiteMap: function () {
            this.mapTaxaSite.once('postcompose', function (event) {
                var canvas = event.context.canvas;
                if (navigator.msSaveBlob) {
                    navigator.msSaveBlob(canvas.msToBlob(), 'map.png');
                } else {
                    canvas.toBlob(function (blob) {
                        saveAs(blob, 'map.png')
                    })
                }
            });
            this.mapTaxaSite.renderSync();
        },
        downloadTaxaRecordsTimeline: function () {
            var title = 'taxa-record-timeline';
            var canvas = this.taxaRecordsTimelineGraph;

            html2canvas(canvas, {
                onrendered: function (canvas) {
                    var link = document.createElement('a');
                    link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
                    link.download = title + '.png';
                    link.click();
                }
            })
        }
    })
});
