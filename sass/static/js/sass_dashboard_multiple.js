let map = null;

function drawMap(data) {
    let scaleLineControl = new ol.control.ScaleLine();
    map = new ol.Map({
        controls: ol.control.defaults().extend([
            scaleLineControl
        ]),
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM({
                    wrapDateLine: false,
                    wrapX: false,
                    noWrap: true
                })
            })
        ],
        target: 'map',
        view: new ol.View({
            center: [0, 0],
            zoom: 2
        })
    });

    let graticule = new ol.Graticule({
        strokeStyle: new ol.style.Stroke({
            color: 'rgba(0,0,0,1)',
            width: 1,
            lineDash: [2.5, 4]
        }),
        showLabels: true
    });

    graticule.setMap(map);
    let iconFeatures = [];
    $.each(data['coordinates'], function (index, coordinate) {
        let iconFeature = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.transform([coordinate['x'], coordinate['y']], 'EPSG:4326', 'EPSG:3857')),
        });
        iconFeatures.push(iconFeature);
    });

    let vectorSource = new ol.source.Vector({
        features: iconFeatures
    });
    let iconStyle = new ol.style.Style({
        image: new ol.style.Icon(({
            anchor: [0.5, 46],
            anchorXUnits: 'fraction',
            anchorYUnits: 'pixels',
            opacity: 0.75,
            src: '/static/img/map-marker.png'
        }))
    });
    let vectorLayer = new ol.layer.Vector({
        source: vectorSource,
        style: iconStyle
    });
    map.addLayer(vectorLayer);
    map.getView().fit(vectorSource.getExtent(), map.getSize());
    let zoom = map.getView().getZoom();
    if (zoom > 10) {
        map.getView().setZoom(10);
    }
}

function renderSassScoreChart(data) {
    // Sass score chart
    let sassScoreData = {
        labels: data['sass_score_chart_data']['site_code'],
        datasets: [{
            label: 'Sass Score',
            backgroundColor: '#589f48',
            borderColor: '#589f48',
            borderWidth: 1,
            data: data['sass_score_chart_data']['sass_score']
        }]
    };
    let taxaCountData = {
        labels: data['sass_score_chart_data']['site_code'],
        datasets: [{
            label: 'Number of taxa',
            backgroundColor: '#589f48',
            borderColor: '#589f48',
            borderWidth: 1,
            data: data['sass_score_chart_data']['taxa_count']
        }]
    };
    let asptScoreData = {
        labels: data['sass_score_chart_data']['site_code'],
        datasets: [{
            label: 'ASPT',
            backgroundColor: '#589f48',
            borderColor: '#589f48',
            borderWidth: 1,
            data: data['sass_score_chart_data']['aspt_score']
        }]
    };
    let options = {
        legend: {
            position: 'bottom'
        },
        tooltips: {
            enabled: true,
            mode: 'single',
            callbacks: {
                afterBody: function (_data) {
                    return 'Date : ' + data['sass_score_chart_data']['date'][_data[0]['index']];
                }
            }
        },
        scales: {
            xAxes: [{
                ticks: {
                    beginAtZero: true
                }
            }]
        },
    };
    let hiddenYAxesLabelOptions = JSON.parse(JSON.stringify(options));
    hiddenYAxesLabelOptions['scales']['yAxes'] = [{
        ticks: {
            display: false
        }
    }];
    hiddenYAxesLabelOptions['tooltips']['callbacks'] = {
        afterBody: function (_data) {
            return 'Date : ' + data['sass_score_chart_data']['date'][_data[0]['index']];
        }
    };

    let sassScoreChart = new Chart(document.getElementById('sass-score-chart'), {
        type: 'horizontalBar',
        data: sassScoreData,
        options: options
    });
    let taxaCountScoreChart = new Chart($('#taxa-numbers-chart'), {
        type: 'horizontalBar',
        data: taxaCountData,
        options: hiddenYAxesLabelOptions
    });
    let asptScoreChart = new Chart($('#aspt-chart'), {
        type: 'horizontalBar',
        data: asptScoreData,
        options: hiddenYAxesLabelOptions
    });
}

function renderSassSummaryTable(data) {
    let siteCodes = data['sass_score_chart_data']['site_code'];
    let table = $('#sass-summary-table');
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let queries = queryString.split('siteId=');

    $.each(siteCodes, function (index, value) {
        let siteUrls = JSON.parse(JSON.stringify(queries));
        siteUrls[0] += 'siteId=' + data['sass_score_chart_data']['site_id'][index] + '&';
        siteUrls[1] = siteUrls[1].substring(siteUrls[1].indexOf('&') + 1);

        let $tr = $('<tr>');
        $tr.append(
            '<td> <a href="/sass/dashboard/' + data['sass_score_chart_data']['site_id'][index] + '/?' + siteUrls.join('') + '">' + value + '</a></td>'
        );
        $tr.append(
            '<td>' + Math.round(data['sass_score_chart_data']['sass_score_average'][index]['avg']) + '(' + data['sass_score_chart_data']['sass_score_average'][index]['min'] + '-' + data['sass_score_chart_data']['sass_score_average'][index]['max'] + ') </td>'
        );
        $tr.append(
            '<td>' + Math.round(data['sass_score_chart_data']['taxa_number_average'][index]['avg']) + '(' + data['sass_score_chart_data']['taxa_number_average'][index]['min'] + '-' + data['sass_score_chart_data']['taxa_number_average'][index]['max'] + ') </td>'
        );
        $tr.append(
            '<td>' + data['sass_score_chart_data']['aspt_average'][index]['avg'].toFixed(2) + '(' + data['sass_score_chart_data']['aspt_average'][index]['min'].toFixed(2) + '-' + data['sass_score_chart_data']['aspt_average'][index]['max'].toFixed(2) + ') </td>'
        );
        $tr.append(
            '<td>' + data['sass_score_chart_data']['number_assessments'][index] + '</td>'
        );
        $tr.append(
            '<td>' + data['sass_score_chart_data']['sass_score'][index] + '</td>'
        );
        $tr.append(
            '<td>' + data['sass_score_chart_data']['taxa_count'][index] + '</td>'
        );
        $tr.append(
            '<td>' + data['sass_score_chart_data']['aspt_score'][index] + '</td>'
        );
        $tr.append(
            '<td> <a href="/sass/view/' + data['sass_score_chart_data']['sass_ids'][index] + '">' + data['sass_score_chart_data']['date'][index] + '</a></td>'
        );

        table.append($tr);
    });
}

function renderTaxaPerBiotopeTable(data) {
    let $table = $('#sass-taxa-per-biotope');
    let tableData = data['taxa_per_biotope_data'];
    let siteCodes = data['sass_score_chart_data']['site_code'];
    let siteIds = data['sass_score_chart_data']['site_id'];
    let dates = data['sass_score_chart_data']['date'];
    let $row1 = $($table.find('.row1')[0]);
    let $row2 = $($table.find('.row2')[0]);
    let biotopeEnum = {
        'stone': 0,
        'veg': 0,
        'gravel': 0,
        'site': 0,
    };
    let numberOfTaxaPerSite = {};
    let totalSassPerSite = {};

    // Create heading
    $.each(siteIds, function (index, siteId) {
        $row1.append(
            '<th colspan="4">' + siteCodes[index] + '<br>' + dates[index] + '</th>'
        );
        $row2.append(
            '<th> S </th> <th> V </th> <th> G </th> <th> Site </th>'
        );
        numberOfTaxaPerSite[siteId] = JSON.parse(JSON.stringify(biotopeEnum));
        totalSassPerSite[siteId] = JSON.parse(JSON.stringify(biotopeEnum));
    });

    // Add data
    let lastTaxonGroup = '';
    $.each(tableData, function (key, _tableData) {
        let taxonGroupName = _tableData['group_name'];
        let $tr = $('<tr>');
        if (lastTaxonGroup === '') {
            lastTaxonGroup = taxonGroupName;
        } else if (lastTaxonGroup !== taxonGroupName) {
            // add border
            lastTaxonGroup = taxonGroupName;
            $tr.addClass('taxon-group');
        } else {
            taxonGroupName = '';
        }
        $tr.append('<td>' + taxonGroupName + '</td>');
        $tr.append('<td>' + _tableData['taxon_name'] + '</td>');
        $tr.append('<td>' + _tableData['score'] + '</td>');

        $.each(siteIds, function (index, siteId) {
            let siteAbundance = _tableData['site_abundance'][siteId];
            let score = _tableData['score'];
            if (typeof siteAbundance === 'undefined') {
                siteAbundance = '';
            } else {
                totalSassPerSite[siteId]['site'] += parseInt(score);
                numberOfTaxaPerSite[siteId]['site'] += 1;
            }
            $tr.append('<td class="stone-' + siteId + '"></td><td class="veg-' + siteId + '"></td><td class="gravel-' + siteId + '"></td><td class="site">' + siteAbundance + '</td>');
            let siteCodeStr = siteId.toString();
            let biotopeData = _tableData['biotope_data'];
            if (typeof biotopeData === 'undefined') {
                return true;
            }
            if (_tableData['biotope_data'].hasOwnProperty(siteCodeStr)) {
                let biotopeData = _tableData['biotope_data'][siteCodeStr];
                $.each(biotopeData, function (biotopeName, abundance) {
                    let lowercaseValue = biotopeName.toLowerCase();
                    let biotope = '';
                    if (lowercaseValue.includes('vegetation') || lowercaseValue.includes('mv') || lowercaseValue.includes('aqv')) {
                        biotope = 'veg';
                    } else if (lowercaseValue.includes('stone') || lowercaseValue.includes('sic') || lowercaseValue.includes('sooc')) {
                        biotope = 'stone';
                    } else {
                        biotope = 'gravel';
                    }

                    totalSassPerSite[siteId][biotope] += parseInt(score);
                    numberOfTaxaPerSite[siteId][biotope] += 1;

                    $tr.find('.' + biotope + '-' + siteId).html(
                        abundance
                    )
                })
            }
        });
        $table.append($tr);
    });
    let $sassScoreTr = $('<tr class="total-table" >');
    $sassScoreTr.append('<td colspan="3"> SASS Score </td>');
    let $taxaNumbersTr = $('<tr class="total-table" >');
    $taxaNumbersTr.append('<td colspan="3"> Number of Taxa </td>');
    let $asptTr = $('<tr class="total-table" >');
    $asptTr.append('<td colspan="3"> ASPT </td>');

    $.each(totalSassPerSite, function (siteId, totalSassScore) {
        $.each(totalSassScore, function (category, value) {
            $sassScoreTr.append('<td>' + value + '</td>');
            $taxaNumbersTr.append('<td>' + numberOfTaxaPerSite[siteId][category] + '</td>');
            if (value && numberOfTaxaPerSite[siteId][category]) {
                $asptTr.append('<td>' + (value / numberOfTaxaPerSite[siteId][category]).toFixed(2) + '</td>');
            } else {
                $asptTr.append('<td> - </td>');
            }
        });
    });
    $table.append($sassScoreTr);
    $table.append($taxaNumbersTr);
    $table.append($asptTr);
}

function renderBiotopeRatingsChart(data) {
    let siteIds = data['sass_score_chart_data']['site_id'];
    let biotopeRatingData = data['biotope_ratings_chart_data']['rating_data'];
    let biotopeRatingLabels = data['biotope_ratings_chart_data']['biotope_labels'];

    let barOptions_stacked = {
        scales: {
            xAxes: [{
                ticks: {
                    beginAtZero: true,
                },
                gridLines: {},
                stacked: true
            }],
            yAxes: [{
                barPercentage: 1,
                gridLines: {
                    display: false,
                    color: "#fff",
                },
                stacked: true
            }]
        },
        responsive: true,
        maintainAspectRatio: false,
    };
    let dataLength = Object.keys(biotopeRatingData).length;
    if (dataLength < 5) {
        $("#biotope-ratings-chart").height(100 * Object.keys(biotopeRatingData).length);
    } else if (dataLength < 15) {
        $("#biotope-ratings-chart").height(50 * Object.keys(biotopeRatingData).length);
    } else {
        $("#biotope-ratings-chart").height(25 * Object.keys(biotopeRatingData).length);
    }

    let ctx = document.getElementById("biotope-ratings-chart");

    let labels = [];
    let datasets = {};
    let datasetsList = [];

    let color = {
        'Stones in current (SIC)': '#1F4E7A',
        'Stones out of current (SOOC)': '#2E76B6',
        'Aquatic vegetation': '#375822',
        'Gravel': '#4E7F31',
        'Sand': '#BE9001',
        'Silt/mud/clay': '#bdbe0d'
    };

    $.each(siteIds, function (index, siteId) {
        if (!biotopeRatingData.hasOwnProperty(siteId)) {
            return true;
        }
        let data = biotopeRatingData[siteId];
        labels.push(biotopeRatingData[siteId]['site_code'] + ' (' + biotopeRatingData[siteId]['date'] + ')');
        $.each(biotopeRatingLabels, function (index, biotopeName) {
            let ratingNumber = 0;
            let datasetsIndex = 0;
            if (data.hasOwnProperty(biotopeName)) {
                ratingNumber = parseInt(data[biotopeName]);
            }
            if (!datasets.hasOwnProperty(biotopeName)) {
                let backgroundColor = "rgba(63,103,126,1)";
                if (color.hasOwnProperty(biotopeName)) {
                    backgroundColor = color[biotopeName];
                }
                datasetsList.push({
                    'label': biotopeName,
                    'data': [],
                    backgroundColor: backgroundColor
                });
                datasetsIndex = datasetsList.length - 1;
                datasets[biotopeName] = datasetsIndex
            } else {
                datasetsIndex = datasets[biotopeName];
            }
            datasetsList[datasetsIndex]['data'].push(ratingNumber);
        });
    });

    let biotopeRatingsChart = new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: labels,
            datasets: datasetsList
        },
        options: barOptions_stacked,
    });
}

function onDownloadCSVClicked(e) {
    let downloadButton = $(e.target);
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/sass/download-sass-data-site/?' + queryString;
    downloadButton.html("Processing...");
    downloadButton.prop("disabled", true);
    downloadCSV(url, downloadButton);
}

function onDownloadChartClicked(e) {
    let wrapper = $(this).parent().parent();
    let button = $(this);
    let title = $(this).data('download-title');
    let $logo = $('.logo').clone();
    button.hide();
    $(wrapper).css({"padding-bottom": "55px"});
    $(wrapper).append($logo.removeClass('hide-logo'));
    let container = $(wrapper);
    html2canvas(wrapper, {
        scale: 1,
        dpi: 144,
        onrendered: function (canvas) {
            $logo.remove();
            container.css({"padding-bottom": "5px"});
            button.show();
            let link = document.createElement('a');
            link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
            link.download = title + '.png';
            link.click();
        }
    })
}

function onDownloadMapClicked(e) {
    map.once('postrender', function (event) {
        var canvas = $('#map');
        html2canvas(canvas, {
            useCORS: true,
            background: '#FFFFFF',
            allowTaint: false,
            onrendered: function (canvas) {
                let link = document.createElement('a');
                link.setAttribute("type", "hidden");
                link.href = canvas.toDataURL("image/png");
                link.download = 'map.png';
                document.body.appendChild(link);
                link.click();
                link.remove();
            }
        });
    });
    map.renderSync();
}

function onDownloadSummaryCSVClicked(e) {
    let downloadButton = $(e.target);
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/sass/download-sass-summary-data/?' + queryString;
    downloadButton.html("Processing...");
    downloadButton.prop("disabled", true);
    downloadCSV(url, downloadButton);
}

function renderDataSources(data) {
    let ulDiv = $('#data-source-list');
    let dataSources = data['data_sources'];
    $.each(dataSources, function (index, source) {
        ulDiv.append('<li>' + source + '</li>')
    });
}

function renderEcologicalChart(data) {
    let $container = $('#ecological-chart-container');
    let ecologicalChartData = data['ecological_chart_data'];
    let rowSize = 12 / ecologicalChartData.length;
    let rowClass = 'col-md-' + rowSize;
    let legendCreated = false;

    if (data['unique_ecoregions'].length > 0) {
        let $ecologicalAlert = $('.ecological-alert');
        $ecologicalAlert.show();
        $ecologicalAlert.append('<br/>');
        let $ul = $('<ul style="padding-top: 10px;">');
        $ecologicalAlert.append($ul);
        $.each(data['unique_ecoregions'], (index, uniqueEcoregion) => {
            let combination = uniqueEcoregion['eco_regions'][0] + '-' + uniqueEcoregion['eco_regions'][1];
            $ul.append('<li>' + combination + '</li>');
        })
    }

    $.each(ecologicalChartData, function (index, chartData) {
        let siteIds = chartData['site_data']['site_ids'];
        let plotData = [];
        $.each(siteIds, (indexSiteId, siteId) => {
            let sassData = data['sass_score_chart_data'];
            let index = sassData['site_id'].indexOf(siteId);
            plotData.push({
                'aspt': sassData['aspt_score'][index],
                'sass': sassData['sass_score'][index],
                'label': sassData['site_code'][index] + ' (' + sassData['date'][index] + ')'
            })
        });

        // Create legend
        if (!legendCreated) {
            legendCreated = true;
            let legendContainer = $('.ecological-legend-container');
            $.each(chartData['chart_data'].reverse(), (indexChartData, boundaryData) => {
                let $legend = $('<span class="ecological-chart-legend">&nbsp;</span>');
                legendContainer.append($legend);
                $legend.after(boundaryData['ec_category']);
                $legend.css('background-color', boundaryData['color']);
            })
        }

        let $div = $('<div>');
        $div.addClass(rowClass);
        let $chartCanvas = $('<canvas>');
        $div.append($chartCanvas);
        createEcologicalChart(
            $chartCanvas,
            chartData['chart_data'],
            plotData,
            true,
            chartData['site_data']['eco_region'] + ' - ' + chartData['site_data']['geo_class']
        );
        $container.append($div);
    });
}

function renderAll(data) {
    drawMap(data);
    renderSassScoreChart(data);
    renderSassSummaryTable(data);
    renderTaxaPerBiotopeTable(data);
    renderBiotopeRatingsChart(data);
    renderDataSources(data);
    renderEcologicalChart(data);
}

$(function () {
    let params = window.location.href.split('dashboard-multi-sites')[1];
    let url = '/sass/dashboard-multi-sites-api' + params;
    $.get({
        url: url,
        dataType: 'json',
        success: function (data) {
            $('.ajax-container').show();
            renderFilterList($('.filter-table'));
            renderAll(data);
        }
    });

    Pace.on('hide', function (context) {
        $('.loading-title').hide();
    });

    $('.download-as-csv').click(onDownloadCSVClicked);
    $('.download-chart').click(onDownloadChartClicked);
    $('.download-map').click(onDownloadMapClicked);
    $('.download-summary-as-csv').click(onDownloadSummaryCSVClicked);
    $('[data-toggle="tooltip"]').tooltip();
});