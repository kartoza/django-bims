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
            this.gbifId = null;
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
            this.mapTaxaSite = null;
            this.csvDownloadsUrl = '/download-csv-taxa-records/';
            this.imagesCard = this.$el.find('#fsdd-images-card-body');
            let biodiversityLayersOptions = {
                url: geoserverPublicUrl + 'wms',
                params: {
                    LAYERS: locationSiteGeoserverLayer,
                    FORMAT: 'image/png8',
                    viewparams: 'where:' + emptyWMSSiteParameter
                },
                ratio: 1,
                serverType: 'geoserver'
            };
            this.siteLayerSource = new ol.source.ImageWMS(biodiversityLayersOptions);
            this.siteTileLayer = new ol.layer.Image({
                source: this.siteLayerSource
            });
            return this;
        },
        show: function (data) {
            var self = this;
            if (this.isOpen) {
                return false;
            }
            this.isOpen = true;
            this.loadingDashboard.show();

            this.$el.show('slide', {
                direction: 'right'
            }, 300, function () {
                self.url = '/api/bio-collection-summary/';
                if (typeof data === 'string') {
                    self.url += '?' + data;
                    self.csvDownloadsUrl += '?' + data;
                } else {
                    self.taxonName = data.taxonName;
                    self.taxonId = data.taxonId;
                    self.siteDetail = data.siteDetail;
                    if (typeof filterParameters !== 'undefined') {
                        self.parameters = filterParameters;
                        self.parameters['taxon'] = self.taxonId;
                    }
                    Shared.Router.updateUrl('species-detail/' + self.apiParameters(filterParameters).substr(1), true);
                    var params = self.apiParameters(self.parameters);
                    self.csvDownloadsUrl += params;
                    self.url += params;
                }

                self.fetchRecords();
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
        displayTaxonomyRank: function (taxonomy_rank) {
            let taxononomyRankList = _.template($('#taxon-detail-table').html());
            this.overviewNameTaxonTable.html(taxononomyRankList({
                kingdom: taxonomy_rank['KINGDOM'],
                phylum: taxonomy_rank['PHYLUM'],
                my_class: taxonomy_rank['CLASS'],
                order: taxonomy_rank['ORDER'],
                family: taxonomy_rank['FAMILY'],
                genus: taxonomy_rank['GENUS'],
                species: taxonomy_rank['SPECIES'],
            }));
        },
        generateDashboard: function (data) {
            var self = this;
            if (data['common_name'] != '')
            {
                this.dashboardTitleContainer.html(data['taxon'] + ' ('
                + data['common_name'] + ')');
            }
            else
            {
                  this.dashboardTitleContainer.html(data['taxon'])
            }
            var gbif_key = data['gbif_id'];
            var taxonomy_id = data['process_id'];
            var canonicalName = data['taxon'];
            var common_name = data['common_name']

            self.taxonName = canonicalName;

            // Set origin
            var category = data['origin'];
            $.each(self.originInfoList.children(), function (key, data) {
                var $originInfoItem = $(data);
                if ($originInfoItem.data('value') === category) {
                    $originInfoItem.css('background-color', 'rgba(5, 255, 103, 0.28)');
                }
            });

            // Set endemic
            var endemic = data['endemism'];
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
            var conservation = data['conservation_status'];
            $.each(this.conservationStatusList.children(), function (key, data) {
                var $conservationStatusItem = $(data);
                if ($conservationStatusItem.data('value') === conservation) {
                    $conservationStatusItem.css('background-color', 'rgba(5, 255, 103, 0.28)');
                }
            });

            var overViewTable = _.template($('#taxon-overview-table').html());
            this.overviewTaxaTable.html(overViewTable({
                csv_downloads_url: self.csvDownloadsUrl,
                count: data['total_records'],
                taxon_class: data['taxon'],
                gbif_id: gbif_key,
                common_name: data['common_name']
            }));

            let recordsOverTimeData = data['records_over_time_data'];
            let recordsOverTimeLabels = data['records_over_time_labels'];
            var recordsOptions = {
                maintainAspectRatio: false,
                title: {display: false, text: 'Records'},
                legend: {display: false},
                scales: {
                    xAxes: [{
                        barPercentage: 0.4,
                        ticks: {
                            autoSkip: false,
                            maxRotation: 90,
                            minRotation: 90
                        },
                        scaleLabel: {display: false, labelString: 'Year'}
                    }],
                    yAxes: [{
                        stacked: true,
                        scaleLabel: {display: true, labelString: 'Occurrence'},
                        ticks: {
                            beginAtZero: true,
                            callback: function (value) {
                                if (value % 1 === 0) {
                                    return value;
                                }
                            },
                        },
                    }]
                }
            };


            var objectDatasets = [{
                data: recordsOverTimeData,
                backgroundColor: 'rgba(222, 210, 65, 1)'
            }];

            this.taxaRecordsTimelineGraphChart = self.createTimelineGraph(
                self.taxaRecordsTimelineGraphCanvas,
                recordsOverTimeLabels,
                objectDatasets,
                recordsOptions);
            this.displayTaxonomyRank(data['taxonomy_rank']);

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
                        zoom: 2
                    })
                });
                this.mapTaxaSite.addLayer(this.siteTileLayer);
            }

            let newParams = {
                layers: locationSiteGeoserverLayer,
                format: 'image/png',
                viewparams: 'where:"' + data['sites_raw_query'] + '"'
            };
            this.siteLayerSource.updateParams(newParams);

             // Zoom to extent
            let ext = ol.proj.transformExtent(data['extent'], ol.proj.get('EPSG:4326'), ol.proj.get('EPSG:3857'));
            this.mapTaxaSite.getView().fit(ext, this.mapTaxaSite.getSize());
            if (this.mapTaxaSite.getView().getZoom() > 8) {
                this.mapTaxaSite.getView().setZoom(8);
            }

            var $tableArea = $('<div class="container"></div>');
            $tableArea.append(`
                    <div class="row">
                    <div class="col-4 title_column">Site name</div>
                    <div class="col-4 title_column">River Name</div>
                    <div class="col-4 title_column">Records</div>
                    </div>`);
            $.each(data['records_per_area'], function (index, areaRecord) {
                let site_name = areaRecord['site_name'];
                let count = areaRecord['count']
                let river_name = 'Unknown'
                $tableArea.append(`
                    <div class="row">
                    <div class="col-4">${site_name}</div>
                    <div class="col-4">${river_name}</div>
                    <div class="col-4">${count}</div>
                    </div>`)
            });
            self.recordsAreaTable.html($tableArea);
            var thirdPartyData = this.renderThirdPartyData(data);
            this.imagesCard.append(thirdPartyData);
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
            this.imagesCard.html('');
            // Clear canvas
            if (this.taxaRecordsTimelineGraphChart) {
                this.taxaRecordsTimelineGraphChart.destroy();
                this.taxaRecordsTimelineGraphChart = null;
            }



            if (this.mapTaxaSite) {
                let newParams = {
                    layers: locationSiteGeoserverLayer,
                    format: 'image/png',
                    viewparams: 'where:' + emptyWMSSiteParameter
                };
                this.siteLayerSource.updateParams(newParams);
            }
            this.recordsTable.html('');
            this.recordsAreaTable.html('');
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
                Shared.Router.clearSearch();
            });
        },
        createTimelineGraph: function (canvas, labels, dataset, options) {
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
            var canvas = this.taxaRecordsTimelineGraph[0];
            this.downloadChart(title, canvas);
        },
        downloadChart: function (title, graph_canvas) {
            var img = new Image();
            var ctx = graph_canvas.getContext('2d');
            img.src='/static/img/bims-stamp.png';
            img.onload = function() {
                ctx.drawImage(img, graph_canvas.scrollWidth - img.width - 5,
                    graph_canvas.scrollHeight - img.height - 5);
                canvas = graph_canvas;
                html2canvas(canvas, {
                    onrendered: function (canvas) {
                        var link = document.createElement('a');
                        link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
                        link.download = title + '.png';
                        link.click();
                    }
                })
            }
        },
        renderThirdPartyData: function (data) {

            var $thirdPartyData = $('<div>');

            var template = _.template($('#third-party-template').html());
            $thirdPartyData.append(template({}));

            var $wrapper = $thirdPartyData.find('.third-party-wrapper');
            var mediaFound = false;
            var $fetchingInfoDiv = $thirdPartyData.find('.third-party-fetching-info');
            var this_GBIF_ID = data['gbif_id'];
            $.get({
                url: 'https://api.gbif.org/v1/occurrence/search?taxonKey='+this_GBIF_ID+'&limit=4',
                dataType: 'json',
                success: function (data) {
                    var results = data['results'];

                    var $rowWrapper = $('<div id="gbif-images-row" class="gbif-images-row row gbif-images-row-fsdd"></div>');

                    var result = {};
                    for (let result_id in results)
                    {
                        var $firstColumnDiv = $('<div class="col-6" "></div>');
                        result = results[result_id];
                        if(!result.hasOwnProperty('media')) {
                            continue;
                        }
                        if(result['media'].length === 0) {
                            continue;
                        }
                        var media = result['media'][0];
                        if(!media.hasOwnProperty('identifier')) {
                            continue;
                        }
                        mediaFound = true;
                        if(mediaFound) {
                            $fetchingInfoDiv.hide();
                        }
                        $firstColumnDiv.append('<a target="_blank" href="'+media['references']+'">' +
                            '<img title="Source: '+media['publisher']+'" alt="'+media['rightsHolder']+'" src="'+media['identifier']+'" width="100%"/></a>');
                        $rowWrapper.append($firstColumnDiv);
                    }
                    $wrapper.append($rowWrapper);
                    if(!mediaFound) {
                        $fetchingInfoDiv.html('Media not found');
                    }
                }
            });

            return $thirdPartyData;
        },
    })
});
