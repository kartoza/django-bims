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
            this.endemismBlockData = this.$el.find('#endemism-block-data');
            this.taxaRecordsTimelineGraphChart = null;
            this.taxaRecordsTimelineGraphCanvas = this.taxaRecordsTimelineGraph[0].getContext('2d');
            this.recordsTable = this.$el.find('.records-table');
            this.recordsAreaTable = this.$el.find('.records-area-table');
            this.mapTaxaSite = null;
            this.csvDownloadsUrl = '/download-csv-taxa-records/';
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
            let taxonomySystem = this.$el.find('.taxon-dashboard-detail');
            $.each(taxonomy_rank, function (rank, name) {
                taxonomySystem.append(
                    '<tr>' +
                    '<td>' + rank + '</td>' +
                    '<td>' + name + '</td>' +
                    '</tr>'
                )
            });
        },
        generateDashboard: function (data) {
            var self = this;
            this.dashboardTitleContainer.html(this.taxonName);
            var gbif_key = data['gbif_id'];
            var taxonomy_id = data['process_id'];
            var canonicalName = data['taxon'];

            self.taxonName = canonicalName;

            // Set origin
            var category = data['origin'];
            $.each(self.originInfoList.children(), function (key, data) {
                var $originInfoItem = $(data);
                if ($originInfoItem.data('value') === category) {
                    $originInfoItem.css('background-color', 'rgba(5, 255, 103, 0.28)');
                }
            });

            var endemism_block_data = {};
            endemism_block_data['value'] = data['endemism'];;
            endemism_block_data['keys'] = ['Widespread', 'Regional endemic', 'Micro-endemic'];
            endemism_block_data['value_title'] = data['endemism'];
            this.endemismBlockData.append(self.renderFBISBlocks(endemism_block_data));

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
                count: data.length,
                taxon_class: data['taxon'],
                gbif_id: gbif_key
            }));

            let taxonDetailTable = _.template($('#taxon-detail-table').html());
            this.overviewNameTaxonTable.html(taxonDetailTable());

            let recordsOverTimeData = data['records_over_time_data'];
            let recordsOverTimeLabels = data['records_over_time_labels'];
            var recordsOptions = {
                maintainAspectRatio: false,
                title: {display: true, text: 'Records'},
                legend: {display: false},
                scales: {
                    xAxes: [{
                        barPercentage: 0.4,
                        ticks: {
                            autoSkip: false,
                            maxRotation: 90,
                            minRotation: 90
                        },
                        scaleLabel: {display: true, labelString: 'Year'}
                    }],
                    yAxes: [{
                        stacked: true,
                        scaleLabel: {display: true, labelString: 'Occurrence'}
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

            var $tableArea = $('<table class="table"></table>');
            $tableArea.append('<tr><th>Site name</th><th>Records</th></tr>');
            $.each(data['records_per_area'], function (index, areaRecord) {
                $tableArea.append('<tr><td>' + areaRecord['site_name'] + '</td><td>' + areaRecord['count'] + '</td></tr>')
            });
            self.recordsAreaTable.html($tableArea);

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
            this.endemismBlockData.html('');

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
        renderFBISBlocks: function(data, stretch_selection = false) {
            var $detailWrapper = $('<div style="padding-left: 0;"></div>');
            $detailWrapper.append(this.getHtmlForFBISBlocks(data, stretch_selection));
            return $detailWrapper;
        },
        getHtmlForFBISBlocks: function (new_data_in, stretch_selection) {
            var result_html = '<div class ="fbis-data-flex-block-row">'
            var data_in = new_data_in;
            var data_value = data_in.value;
            var data_title = data_in.value_title;
            var keys = data_in.keys;
            var key = '';
            var style_class = '';
            var for_count = 0;
            for (let key of keys) {
                for_count += 1;
                style_class = "fbis-rpanel-block fbis-rpanel-block-dd ";
                var temp_key = key;
                //Highlight my selected box with a different colour
                if (key == data_value) {
                    style_class += " fbis-rpanel-block-selected";
                    temp_key = data_title;
                    if (stretch_selection == true)
                    {
                        style_class += " flex-base-auto";
                    }
                }
                result_html += (`<div class="${style_class}">
                                 <div class="fbis-rpanel-block-text">
                                 ${temp_key}</div></div>`)

            };
            result_html += '</div>';
            return result_html;
        },

    })
});
