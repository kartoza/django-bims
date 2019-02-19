function drawMap(data) {
    let scaleLineControl = new ol.control.ScaleLine();
    let map = new ol.Map({
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
            color: 'rgba(255,120,0,0.9)',
            width: 2,
            lineDash: [0.5, 4]
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
        responsive: true,
        maintainAspectRatio: false,
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

    $("#sass-score-chart").height(18 * sassScoreData['labels'].length);
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
    $.each(siteCodes, function (index, value) {
        let $tr = $('<tr>');
        $tr.append(
            '<td>' + value + '</td>'
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
    $.each(tableData, function (key, _tableData) {
        let $tr = $('<tr>');
        $tr.append('<td>' + _tableData['canonical_name'] + '</td>');
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
    if (dataLength < 10) {
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

function renderAll(data) {
    drawMap(data);
    renderSassScoreChart(data);
    renderSassSummaryTable(data);
    renderTaxaPerBiotopeTable(data);
    renderBiotopeRatingsChart(data);
}

$(function () {
    let params = window.location.href.split('dashboard-multi-sites')[1];
    let url = '/sass/dashboard-multi-sites-api' + params;
    $.get({
        url: url,
        dataType: 'json',
        success: function (data) {
            $('.ajax-container').show();
            renderAll(data);
        }
    });

    Pace.on('hide', function (context) {
        $('.loading-title').hide();
    })
});