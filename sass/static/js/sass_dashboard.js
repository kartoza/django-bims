function drawMap() {
    let map = new ol.Map({
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })
        ],
        target: 'map',
        view: new ol.View({
            center: [0, 0],
            zoom: 2
        })
    });
}

function renderSASSSummaryChart() {
    let data = {
        'labels': yearLabels,
        'datasets': [{
            'label': 'SASS Scores',
            'data': sassScores,
            'backgroundColor': '#589f48',
            'fill': 'false',
        }]
    };
    let taxaNumberData = {
        'labels': yearLabels,
        'datasets': [{
            'label': 'Number of Taxa',
            'data': taxaNumbers,
            'backgroundColor': '#589f48',
            'fill': 'false',
        }]
    };
    let asptData = {
        'labels': yearLabels,
        'datasets': [{
            'label': 'ASPT',
            'data': asptList,
            'backgroundColor': '#589f48',
            'fill': 'false',
        }]
    };
    let options = {};
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
    let table = $('#sass-taxon-per-biotope');
    $.each(sassTaxonData, function (index, value) {
        let $tr = $('<tr data-id="' + value['sass_taxon_id'] + '">');
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
    });

    $.each(biotopeData, function (index, value) {
        let sassTaxonId = value['sass_taxon'];
        let $tr = table.find("[data-id='" + sassTaxonId + "']");
        if (!$tr) {
            return true;
        }
        let lowercaseValue = value['biotope__name'].toLowerCase();
        let $td = $('<div>');
        if (lowercaseValue.includes('vegetation')) {
            $td = $tr.find('.veg');
        } else if (lowercaseValue.includes('stone')) {
            $td = $tr.find('.stone');
        } else {
            $td = $tr.find('.gravel');
        }
        $td.html(value['taxon_abundance__abc']);
    });
}

function renderSensitivityChart() {
    let options = {};
    console.log(sensitivityChartData);
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
