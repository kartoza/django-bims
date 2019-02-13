function drawMap() {
    let scaleLineControl = new ol.control.ScaleLine();
    let map = new ol.Map({
        controls: ol.control.defaults().extend([
            scaleLineControl
        ]),
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM({
                    wrapX: false
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

    // Map marker
    let iconFeatures = [];
    let iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.transform(coordinates, 'EPSG:4326', 'EPSG:3857')),
        name: siteCode,
    });
    iconFeatures.push(iconFeature);
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
    map.getView().setZoom(10);
}

function renderSASSSummaryChart() {
    let data = {
        'labels': dateLabels,
        'datasets': [{
            'label': 'SASS Scores',
            'data': sassScores,
            'backgroundColor': '#589f48',
            'fill': 'false',
        }]
    };
    let taxaNumberData = {
        'labels': dateLabels,
        'datasets': [{
            'label': 'Number of Taxa',
            'data': taxaNumbers,
            'backgroundColor': '#589f48',
            'fill': 'false',
        }]
    };
    let asptData = {
        'labels': dateLabels,
        'datasets': [{
            'label': 'ASPT',
            'data': asptList,
            'backgroundColor': '#589f48',
            'fill': 'false',
        }]
    };
    let scalesOption = {
        xAxes: [{
            display: false
        }],
        yAxes: [{
            ticks: {
                beginAtZero: true
            }
        }]
    };
    let options = {
        scales: scalesOption
    };
    let sassScoreChart = new Chart($('#sass-score-chart'), {
        type: 'bar',
        data: data,
        options: options
    });
    let taxaNumberChart = new Chart($('#taxa-numbers-chart'), {
        type: 'bar',
        data: taxaNumberData,
        options: options
    });
    let asptChart = new Chart($('#aspt-chart'), {
        type: 'bar',
        data: asptData,
        options: {
            scales: scalesOption,
            tooltips: {
                callbacks: {
                    label: function (tooltipItem, chart) {
                        var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
                        return 'ASPT : ' + tooltipItem.yLabel.toFixed(2);
                    }
                }
            }
        }
    });
}

function renderSASSTaxonPerBiotope() {
    let sassTaxon = {};
    let totalSass = {
        'stone': 0,
        'veg': 0,
        'gravel': 0,
        'site': 0
    };
    let numberOfTaxa = {
        'stone': 0,
        'veg': 0,
        'gravel': 0,
        'site': 0,
    };

    let table = $('#sass-taxon-per-biotope');
    $.each(sassTaxonData, function (index, value) {
        let $tr = $('<tr data-id="' + value['sass_taxon_id'] + '" data-weight="' + value['sass_score'] + '">');
        if (sassTaxon.hasOwnProperty(value['taxonomy__canonical_name'])) {
            $tr.append('<td></td>');
            $tr.insertAfter(sassTaxon[value['taxonomy__canonical_name']]);
        } else {
            sassTaxon[value['taxonomy__canonical_name']] = $tr;
            $tr.append('<td>' +
                value['taxonomy__canonical_name'] +
                '</td>');
            table.append($tr);
        }
        sassTaxon[value['taxonomy__canonical_name']] = $tr;
        $tr.append('<td>' +
            value['sass_taxon_name'] +
            '</td>');
        $tr.append('<td>' +
            value['sass_score'] +
            '</td>');
        $tr.append('<td class="stone">' +
            '</td>');
        $tr.append('<td class="veg">' +
            '</td>');
        $tr.append('<td class="gravel">' +
            '</td>');
        $tr.append('<td class="gravel">' +
            value['taxon_abundance__abc'] +
            '</td>');
        totalSass['site'] += parseInt(value['sass_score']);
        numberOfTaxa['site'] += 1;
    });

    // SASS Score total
    let $sassScoreTr = $('<tr class="total-table" id="sass-score-total">');
    $sassScoreTr.append('<td colspan="3">SASS Score</td>');
    $sassScoreTr.append('<td class="stone">-</td>');
    $sassScoreTr.append('<td class="veg">-</td>');
    $sassScoreTr.append('<td class="gravel">-</td>');
    $sassScoreTr.append('<td class="site">-</td>');
    table.append($sassScoreTr);

    // Number of taxa
    let $numberTaxaTr = $('<tr class="total-table" id="number-taxa">');
    $numberTaxaTr.append('<td colspan="3">Number of Taxa</td>');
    $numberTaxaTr.append('<td class="stone">-</td>');
    $numberTaxaTr.append('<td class="veg">-</td>');
    $numberTaxaTr.append('<td class="gravel">-</td>');
    $numberTaxaTr.append('<td class="site">-</td>');
    table.append($numberTaxaTr);

    // ASPT
    let $asptTr = $('<tr class="total-table" id="total-aspt">');
    $asptTr.append('<td colspan="3">ASPT</td>');
    $asptTr.append('<td class="stone">-</td>');
    $asptTr.append('<td class="veg">-</td>');
    $asptTr.append('<td class="gravel">-</td>');
    $asptTr.append('<td class="site">-</td>');
    table.append($asptTr);

    $.each(biotopeData, function (index, value) {
        let sassTaxonId = value['sass_taxon'];
        let $tr = table.find("[data-id='" + sassTaxonId + "']");
        if (!$tr) {
            return true;
        }
        let lowercaseValue = value['biotope__name'].toLowerCase();
        let biotope = '';
        if (lowercaseValue.includes('vegetation')) {
            biotope = 'veg';
        } else if (lowercaseValue.includes('stone')) {
            biotope = 'stone';
        } else {
            biotope = 'gravel';
        }
        let $td = $tr.find('.' + biotope);
        if ($tr.data('weight')) {
            totalSass[biotope] += parseInt($tr.data('weight'));
            numberOfTaxa[biotope] += 1;
        }
        $td.html(value['taxon_abundance__abc']);
    });

    $.each(totalSass, function (index, value) {
        $sassScoreTr.find('.' + index).html(value);
        $numberTaxaTr.find('.' + index).html(numberOfTaxa[index]);
        if (value && numberOfTaxa[index]) {
            $asptTr.find('.' + index).html(parseFloat(value / numberOfTaxa[index]).toFixed(2))
        }
    });
}

function renderSensitivityChart() {
    let options = {};
    let data = {
        datasets: [{
            data: [
                sensitivityChartData['highly_sensitive'],
                sensitivityChartData['sensitive'],
                sensitivityChartData['tolerant'],
                sensitivityChartData['highly_tolerant']
            ],
            backgroundColor: [
                "#4dcfff",
                "#5cff8b",
                "#ffee66",
                "#ff5d49"
            ]
        }],
        labels: [
            'Highly Sensitive',
            'Sensitive',
            'Tolerant',
            'Highly Tolerant'
        ],
    };
    let sensitivityChart = new Chart($('#sensitivity-chart'), {
        type: 'pie',
        data: data,
        options: options
    });
}

$(function () {
    drawMap();
    renderSASSSummaryChart();
    renderSASSTaxonPerBiotope();
    renderSensitivityChart();
});
