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
            'fill': 'false',
        }]
    };
    let taxaNumberData = {
        'labels': yearLabels,
        'datasets': [{
            'label': 'Number of Taxa',
            'data': taxaNumbers,
            'fill': 'false',
        }]
    };
    let asptData = {
        'labels': yearLabels,
        'datasets': [{
            'label': 'ASPT',
            'data': asptList,
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

$(function () {
    drawMap();
    renderSASSSummaryChart();
});