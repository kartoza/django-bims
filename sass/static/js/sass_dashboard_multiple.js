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

function renderAll(data) {
    drawMap(data);
    renderSassScoreChart(data);
    renderSassSummaryTable(data);
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