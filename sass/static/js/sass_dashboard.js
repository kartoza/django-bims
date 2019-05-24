let map = null;

function drawMap() {
    let scaleLineControl = new ol.control.ScaleLine();
    map = new ol.Map({
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
            color: 'rgba(0,0,0,1)',
            width: 1,
            lineDash: [2.5, 4]
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
    // Process data by ecological
    let sassChartBackgroundColor = [];
    let defaultColor = '#c6c6c6';

    $.each(sassScores, function (sasScoreIndex, sassScore) {
        let foundColor = false;
        $.each(ecologicalChartData, function (index, ecologicalData) {
            if (sassScore > ecologicalData['sass_score_precentile'] || asptList[sasScoreIndex] > ecologicalData['aspt_score_precentile']) {
                sassChartBackgroundColor.push(ecologicalData['ecological_colour']);
                foundColor = true;
                return false;
            }
        });
        if (!foundColor) {
            sassChartBackgroundColor.push(defaultColor);
        }
    });

    let data = {
        'labels': dateLabels,
        'datasets': [{
            'label': 'SASS Scores',
            'data': sassScores,
            'backgroundColor': sassChartBackgroundColor,
            'fill': 'false',
        }]
    };
    let taxaNumberData = {
        'labels': dateLabels,
        'datasets': [{
            'label': 'Number of Taxa',
            'data': taxaNumbers,
            'backgroundColor': sassChartBackgroundColor,
            'fill': 'false',
        }]
    };
    let asptData = {
        'labels': dateLabels,
        'datasets': [{
            'label': 'ASPT',
            'data': asptList,
            'backgroundColor': sassChartBackgroundColor,
            'fill': 'false',
        }]
    };

    function scalesOptionFunction(label) {
        return {
            yAxes: [{
                ticks: {
                    beginAtZero: true
                },
                scaleLabel: {
                    display: true,
                    labelString: label
                }
            }]
        };
    }

    function optionsFunction(label) {
        return {
            scales: scalesOptionFunction(label),
            legend: {
                display: false
            }
        };
    }

    let sassScoreChart = new Chart($('#sass-score-chart'), {
        type: 'bar',
        data: data,
        options: optionsFunction('SASS Scores')
    });

    let taxaNumberChart = new Chart($('#taxa-numbers-chart'), {
        type: 'bar',
        data: taxaNumberData,
        options: optionsFunction('Number of Taxa')
    });

    let asptChart = new Chart($('#aspt-chart'), {
        type: 'bar',
        data: asptData,
        options: {
            scales: scalesOptionFunction('ASPT'),
            tooltips: {
                callbacks: {
                    label: function (tooltipItem, chart) {
                        var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
                        return 'ASPT : ' + tooltipItem.yLabel.toFixed(2);
                    }
                }
            },
            legend: {
                display: false
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
    let lastTaxonGroup = '';
    $.each(sassTaxonData, function (index, value) {
        let $tr = $('<tr data-id="' + value['sass_taxon_id'] + '" data-weight="' + value['sass_score'] + '">');
        let taxonGroupName = value['taxonomy__taxongroup__name'];

        if (lastTaxonGroup === '') {
            lastTaxonGroup = taxonGroupName;
        } else if (lastTaxonGroup !== taxonGroupName) {
            // add border
            lastTaxonGroup = taxonGroupName;
            $tr.addClass('taxon-group');
        } else {
            taxonGroupName = '';
        }

        $tr.append('<td>' +
            taxonGroupName +
            '</td>');
        table.append($tr);
        sassTaxon[value['taxonomy__canonical_name']] = $tr;
        if (value['sass_taxon_name']) {
            $tr.append('<td>' +
                value['sass_taxon_name'] +
                '</td>');
        } else {
            $tr.append('<td>' +
                value['taxonomy__canonical_name'] +
                '</td>');
        }
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
    $sassScoreTr.append('<td>SASS Score</td>');
    $sassScoreTr.append('<td> </td>');
    $sassScoreTr.append('<td> </td>');
    $sassScoreTr.append('<td class="stone">-</td>');
    $sassScoreTr.append('<td class="veg">-</td>');
    $sassScoreTr.append('<td class="gravel">-</td>');
    $sassScoreTr.append('<td class="site">-</td>');
    table.append($sassScoreTr);

    // Number of taxa
    let $numberTaxaTr = $('<tr class="total-table" id="number-taxa">');
    $numberTaxaTr.append('<td>Number of Taxa</td>');
    $numberTaxaTr.append('<td> </td>');
    $numberTaxaTr.append('<td> </td>');
    $numberTaxaTr.append('<td class="stone">-</td>');
    $numberTaxaTr.append('<td class="veg">-</td>');
    $numberTaxaTr.append('<td class="gravel">-</td>');
    $numberTaxaTr.append('<td class="site">-</td>');
    table.append($numberTaxaTr);

    // ASPT
    let $asptTr = $('<tr class="total-table" id="total-aspt">');
    $asptTr.append('<td>ASPT</td>');
    $asptTr.append('<td> </td>');
    $asptTr.append('<td> </td>');
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
        if (lowercaseValue.includes('vegetation') || lowercaseValue.includes('mv') || lowercaseValue.includes('aqv')) {
            biotope = 'veg';
        } else if (lowercaseValue.includes('stone') || lowercaseValue.includes('sic') || lowercaseValue.includes('sooc')) {
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
    let options = {
        tooltips: {
            callbacks: {
                label: function (tooltipItem, chartData) {
                    let index = tooltipItem['index'];
                    let label = chartData['labels'][index];
                    return label;
                }
            }
        }
    };
    let data = {
        datasets: [{
            data: [
                sensitivityChartData['highly_sensitive'],
                sensitivityChartData['sensitive'],
                sensitivityChartData['tolerant'],
                sensitivityChartData['highly_tolerant']
            ],
            backgroundColor: [
                "#027EC6",
                "#007236",
                "#FBA618",
                "#ED1B24"
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
    let latestIndex = dateLabels.length - 1;
    $('#sc-latest-sass-record').html('(<a href="/sass/view/' + sassIds[latestIndex] + '">' + dateLabels[latestIndex] + '</a>)');
}

function renderBiotopeRatingsChart() {
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
        }
    };

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

    $.each(dateLabels, function (index, date) {
        if (!biotopeRatingData.hasOwnProperty(date)) {
            return true;
        }
        let data = biotopeRatingData[date];
        labels.push(date);
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

function hexToRgb(hex) {
    let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

let ecoregionChartDotsLabel = {};

function createBoundaryDataset(x, y, color) {
    let rgb = hexToRgb(color);
    return {
        type: 'scatter',
        fill: false,
        lineTension: 0,
        pointRadius: 0,
        pointHitRadius: 0,
        pointHoverRadius: 0,
        showTooltips: false,
        label: 'hide',
        data: [
            {"x": 0, "y": y},
            {"x": x, "y": y},
            {"x": x, "y": 0}
        ],
        showLine: true,
        borderColor: "#000",
        borderWidth: 0.5
    };
}

function createEcologicalScatterDataset(colour, label, data) {
    let rgb = hexToRgb(colour);
    return {
        type: 'scatter',
        fill: true,
        label: label,
        showLine: false,
        showTooltips: false,
        data: data,
        backgroundColor: "rgba(" + rgb['r'] + ", " + rgb['g'] + ", " + rgb['b'] + ", 1)",
        borderColor: null
    }
}

function renderEcologicalCategoryChart() {
    let header = $('.ecological-chart-header');
    try {
        let headerLabel = `${ecoGeoGroup['eco_region']['value']} - ${ecoGeoGroup['geo_class']['value']}`;
        header.html(headerLabel);
    } catch (e) {
    }

    let canvasChart = $('#ecological-category-chart');
    var options = {
        hover: {
            intersect: true
        },
        legend: {
            reverse: true,
            labels: {
                filter: function (item, chart) {
                    return !item.text.includes('hide');
                }
            }
        },
        scales: {
            yAxes: [{
                display: true,
                ticks: {
                    suggestedMin: 0,
                    suggestedMax: 10
                },
                scaleLabel: {
                    display: true,
                    labelString: 'ASPT'
                }
            }],
            xAxes: [{
                type: 'linear',
                position: 'bottom',
                display: true,
                ticks: {
                    suggestedMin: 0,
                    suggestedMax: 200
                },
                scaleLabel: {
                    display: true,
                    labelString: 'SASS Score'
                }
            }]
        },
        tooltips: {
            callbacks: {
                title: function (tooltipItems, data) {
                    let label = '-';
                    let dotIdentifier = tooltipItems[0]['xLabel'] + '-' + parseFloat(tooltipItems[0]['yLabel']).toFixed(2);
                    if (ecoregionChartDotsLabel.hasOwnProperty(dotIdentifier)) {
                        label = ecoregionChartDotsLabel[dotIdentifier];
                    }
                    return label;
                },
                label: function (tooltipItem, data) {
                    let label = data.datasets[tooltipItem.datasetIndex].label || '';
                    if (label) {
                        label += ': ';
                    }
                    label += 'SASS Score: ' + tooltipItem.xLabel + ', ASPT: ' + tooltipItem.yLabel;
                    return label;
                }
            }
        }
    };

    let dataSets = [];
    let scatterDatasets = {};

    // CREATE BOUNDARIES
    $.each(ecologicalChartData, function (index, ecologicalData) {
        dataSets.unshift(createBoundaryDataset(
            ecologicalData['sass_score_precentile'],
            ecologicalData['aspt_score_precentile'],
            ecologicalData['ecological_colour'])
        );
        let ecologicalColor = ecologicalData['ecological_colour'];
        let ecologicalCategoryName = ecologicalData['ecological_category_name'];
        if (!scatterDatasets.hasOwnProperty(ecologicalCategoryName)) {
            scatterDatasets[ecologicalCategoryName] = createEcologicalScatterDataset(
                ecologicalColor,
                ecologicalCategoryName,
                []
            );
        }
    });

    // CREATE SCATTERED DOTS
    let reverseEcologicalChartData = ecologicalChartData;
    $.each(sassScores, function (index, sassScore) {
        let asptScore = asptList[index];
        let scatterData = null;
        $.each(reverseEcologicalChartData, function (index, ecologicalData) {
            let ecologicalCategoryName = ecologicalData['ecological_category_name'];
            if (sassScore > ecologicalData['sass_score_precentile'] || asptScore > ecologicalData['aspt_score_precentile']) {
                scatterData = {
                    'label': ecologicalCategoryName,
                    'x': sassScore,
                    'y': asptScore.toFixed(2)
                };
                // Break loop
                return false;
            }
        });
        if (scatterData) {
            let dotIdentifier = scatterData['x'] + '-' + scatterData['y'];
            if (!ecoregionChartDotsLabel.hasOwnProperty(dotIdentifier)) {
                ecoregionChartDotsLabel[dotIdentifier] = '';
            }
            if (ecoregionChartDotsLabel[dotIdentifier]) {
                ecoregionChartDotsLabel[dotIdentifier] += ', ';
            }
            ecoregionChartDotsLabel[dotIdentifier] += dateLabels[index];
            scatterDatasets[scatterData['label']]['data'].push({
                'x': scatterData['x'],
                'y': scatterData['y'],
                'id': 1
            });
            scatterData = null;
        }
    });

    for (let key in scatterDatasets) {
        dataSets.unshift(scatterDatasets[key]);
    }

    let ecologicalChart = new Chart(canvasChart, {
        type: "bar",
        labels: [],
        data: {
            datasets: dataSets
        },
        options: options
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

function onDownloadSummaryCSVClicked(e) {
    let downloadButton = $(e.target);
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/sass/download-sass-summary-data/?' + queryString;
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

function renderLocationContextTable() {
    let $table = $('.sass-summary tbody');
    let tableData = {
        'Geomorphological zones': '-',
        'Province': '-',
        'Water Management Area': '-',
        'Sub Water Management Area': '-',
        'River Management Unit': '-',
        'Primary Catchment': '-',
        'Secondary Catchment': '-',
        'Tertiary Catchment': '-',
        'Quaternary Catchment': '-',
        'SA Ecoregion': '-',
        'National Critical Biodiversity': '-',
    };
    
    if(ecoGeoGroup) {
        try {
            tableData['Geomorphological zones'] = ecoGeoGroup['geo_class_recoded']['value'];
            tableData['SA Ecoregion'] = ecoGeoGroup['eco_region']['value'];
            tableData['National Critical Biodiversity'] = ecoGeoGroup['national_cba']['value'];
        } catch (e) {
        }
    }
    
    if (politicalBoundary) {
        try {
            tableData['Province'] = politicalBoundary['sa_provinces']['value'];
        } catch (e) {
        }
    }
    
    if (riverCatchments) {
        try {
            tableData['Primary Catchment'] = riverCatchments['primary_catchment_area']['value'];
            tableData['Secondary Catchment'] = riverCatchments['secondary_catchment_area']['value'];
            tableData['Tertiary Catchment'] = riverCatchments['tertiary_catchment_area']['value'];
            tableData['Water Management Area'] = riverCatchments['water_management_area']['value'];
            tableData['Quaternary Catchment'] = riverCatchments['quaternary_catchment_area']['value'];
        } catch (e) {
        }
    }

    $.each(tableData, function (key, value) {
        $table.append('<tr>\n' +
            '<th scope="row"> ' + key + ' </th>' +
            '<td>' + value + '</td>\n' +
            '</tr>');
    });
}

function renderMetricsData() {
    let $table = $('.sass-metrics-table tbody');
    $table.append('<tr>\n' +
        '<td> SASS Score </td>\n' +
        '<td>' + arrAvg(sassScores).toFixed(0) + '</td>\n' +
        '<td>' + Math.min(...sassScores) + '</td>\n' +
        '<td>' + Math.max(...sassScores) + '</td>\n' +
        '</tr>');
    $table.append('<tr>\n' +
        '<td> Number of Taxa </td>\n' +
        '<td>' + arrAvg(taxaNumbers).toFixed(0) + '</td>\n' +
        '<td>' + Math.min(...taxaNumbers) + '</td>\n' +
        '<td>' + Math.max(...taxaNumbers) + '</td>\n' +
        '</tr>');
    $table.append('<tr>\n' +
        '<td> ASPT </td>\n' +
        '<td>' + arrAvg(asptList).toFixed(2) + '</td>\n' +
        '<td>' + Math.min(...asptList).toFixed(2) + '</td>\n' +
        '<td>' + Math.max(...asptList).toFixed(2) + '</td>\n' +
        '</tr>');
}

$(function () {
    drawMap();

    if (sassExists) {
        renderSASSSummaryChart();
        renderSASSTaxonPerBiotope();
        renderSensitivityChart();
        renderBiotopeRatingsChart();
        renderLocationContextTable();
        renderEcologicalCategoryChart();
        renderMetricsData();
        if (dateLabels) {
            $('#earliest-record').html(moment(dateLabels[0], 'DD-MM-YYYY').format('MMMM D, Y'));
            $('#latest-record').html(moment(dateLabels[dateLabels.length - 1], 'DD-MM-YYYY').format('MMMM D, Y'));
            $('#number-of-sass-record').html(dateLabels.length);
        }
    }
    $('.download-as-csv').click(onDownloadCSVClicked);
    $('.download-summary-as-csv').click(onDownloadSummaryCSVClicked);
    $('.download-latest-as-csv').on('click', function () {
        var filename = 'SASS_Taxa_per_biotope_' + sassLatestData;
        exportTableToCSV(filename + '.csv', "sass-taxon-per-biotope-table")
    });

    $('[data-toggle="tooltip"]').tooltip();
    $('.download-chart').click(onDownloadChartClicked);
    $('.download-map').click(onDownloadMapClicked);
});
