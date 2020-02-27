let map = null;
let svgCanvases = {};
let chemSvgCanvases = {};

function createFakeChart(key, chartConfig, displayLegend = true, additionalLegendConfiguration = null) {
    // To convert the chart to svg;
    chartConfig.options['animation'] = false;
    chartConfig.options['responsive'] = false;
    chartConfig.options['legend'] = {
        'display': displayLegend
    };
    if (additionalLegendConfiguration) {
        let legend = chartConfig.options['legend'];
        for (let key in additionalLegendConfiguration) {
            if (legend.hasOwnProperty(key)) {
                legend[key] = Object.assign({}, legend[key], additionalLegendConfiguration[key]);
            } else {
                legend[key] = additionalLegendConfiguration[key];
            }
        }
    }
    svgCanvases[key] = C2S(600, 600);
    new Chart(svgCanvases[key], chartConfig);
}

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

    let chartConfig = {
        type: 'bar',
        data: data,
        options: optionsFunction('SASS Scores')
    };
    new Chart($('#sass-score-chart'), chartConfig);
    createFakeChart('SASS-scores', chartConfig, false);

    chartConfig = {
        type: 'bar',
        data: taxaNumberData,
        options: optionsFunction('Number of Taxa')
    };
    new Chart($('#taxa-numbers-chart'), chartConfig);
    createFakeChart('number-of-taxa', chartConfig, false);

    chartConfig = {
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
    };
    new Chart($('#aspt-chart'), chartConfig);
    createFakeChart('ASPT', chartConfig, false);
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
    let chartConfig = {
        type: 'pie',
        data: data,
        options: options
    };
    new Chart($('#sensitivity-chart'), chartConfig);
    createFakeChart('proportion-of-sensitive', chartConfig);
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
        'Silt/mud/clay': '#bdbe0d',
        'Bedrock': '#8D2641',
        'Marginal vegetation in current (MVIC)': '#B77282',
        'Marginal vegetation out of current (MVOC)': '#18A090'
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

    let chartConfig = {
        type: 'horizontalBar',
        data: {
            labels: labels,
            datasets: datasetsList
        },
        options: barOptions_stacked,
    };
    new Chart(ctx, chartConfig);
    createFakeChart('biotope-ratings', chartConfig, true);
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
    let geoName = '';
    try {
        geoName = geomorphologicalGroup['geo_class'];
    } catch (e) {
    }
    if (useCombinedGeo) {
        geoName = 'Combine';
    }
    try {
        let headerLabel = `${riverEcoregionGroup['eco_region_1']} - ${geoName}`;
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
    let chartConfig = {
        type: "bar",
        labels: [],
        data: {
            datasets: dataSets
        },
        options: options
    };
    new Chart(canvasChart, chartConfig);
    createFakeChart('ecological-category', chartConfig, true, {
        reverse: true,
        labels: {
            filter: function (item, chart) {
                return !item.text.includes('hide');
            }
        }
    });
}

function getCsvName(title, identifier) {
    if (identifier) {
        title += ` for ${identifier}`;
    }
    return title;
}

function onDownloadCSVClicked(e) {
    let downloadButton = $(e.target);
    let csv_name = getCsvName('SASS data', downloadButton.data('identifier'));
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/sass/download-sass-data-site/?' + queryString;
    downloadButton.html("Processing...");
    downloadButton.prop("disabled", true);
    downloadCSV(url, downloadButton, csv_name);
}

function onDownloadChemCSVClicked(e) {
    let downloadButton = $(e.target);
    let csv_name = getCsvName('Chem data', downloadButton.data('identifier'));
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/api/chemical-record/download/?' + queryString;
    downloadButton.html("Processing...");
    downloadButton.prop("disabled", true);
    downloadCSV(url, downloadButton, csv_name);
}

function onDownloadSummaryCSVClicked(e) {
    let downloadButton = $(e.target);
    let csv_name = getCsvName('SASS summary data', downloadButton.data('identifier'));
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/sass/download-sass-summary-data/?' + queryString;
    downloadButton.html("Processing...");
    downloadButton.prop("disabled", true);
    downloadCSV(url, downloadButton, csv_name);
}

function onDownloadChartNewClicked(e) {
    let target = $(e.target);
    if (target.hasClass('processing')) {
        return;
    } else {
        target.addClass('processing');
    }
    let downloadedCharts = 0;
    let chemGraph = false;
    let title = target.data('download-title');
    let charts = target.data('download-chart').split(',');
    let canvases = svgCanvases;
    if (charts[0] === 'chem-graph') {
        charts = Object.keys(chemSvgCanvases);
        canvases = chemSvgCanvases;
        title = '';
        chemGraph = true;
    } else {
        if (charts.length > 1) {
            title +=  ' - ';
        }
    }
    let maxRetry = 10;
    let retry = 0;
    while (!target.hasClass('chart-container') && retry < maxRetry)  {
        target = target.parent();
        retry += 1;
    }
    for (let i=0; i < charts.length; i++) {
        let chart = charts[i];
        let svg = canvases[chart].getSerializedSvg(true);
        let width = canvases[chart].width;
        let height = canvases[chart].height;
        let chartTitle = title;
        if (charts.length > 1) {
            chartTitle += chart.replace(/-/g, ' ').charAt(0).toUpperCase() + chart.replace(/-/g, ' ').slice(1);
        }
        if (chemGraph) {
            chartTitle = chartTitle.replace('/', ' per ');
        }
        $.ajax({
            type: 'POST',
            url: '/svg_to_pdf/',
            data: {
                'svg': svg,
                'title': chartTitle,
                'svgHeight': height,
                'svgWidth': width,
            },
            success: function (response) {
                let urls = response.split('/');
                let link = document.createElement('a');
                link.href = response;
                link.download = urls[urls.length - 1];
                link.dispatchEvent(new MouseEvent('click'));
                downloadedCharts += 1;
                if (downloadedCharts === i + 1) {
                    $(e.target).removeClass('processing');
                }
            }
        });
    }
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
        'Geomorphological zone': '-',
        'Refined Geomorphological zone': refinedGeomorphologicalZone,
        'Catchments': 'title',
        'Primary Catchment': '-',
        'Secondary Catchment': '-',
        'Tertiary Catchment': '-',
        'Quaternary Catchment': '-',
        'Management Areas': 'title',
        'Water Management Area': '-',
        'Sub Water Management Area': '-',
        'River Management Unit': '-',
        'Ecoregion and Province': 'title',
        'SA Ecoregion Level 1': '-',
        'SA Ecoregion Level 2': '-',
        'Freshwater Ecoregion': '-',
        'Province': '-',
    };
    try {
        tableData['Geomorphological zone'] = geomorphologicalGroup['geo_class_recoded'];
        tableData['SA Ecoregion Level 1'] = riverEcoregionGroup['eco_region_1'];
        tableData['SA Ecoregion Level 2'] = riverEcoregionGroup['eco_region_2'];
        tableData['Sub Water Management Area'] = waterManagementAreaGroup['sub_wmas'];
        tableData['Water Management Area'] = waterManagementAreaGroup['water_management_area'];
    } catch (e) {
    }

    let freshwaterEcoregionValue = '-';
    if(freshwaterEcoregion.hasOwnProperty('feow_hydrosheds')) {
        if (freshwaterEcoregion['feow_hydrosheds'] !== 'None') {
            freshwaterEcoregionValue = freshwaterEcoregion['feow_hydrosheds'];
        }
    }
    tableData['Freshwater Ecoregion'] = freshwaterEcoregionValue;

    if (originalGeomorphologicalZone) {
        tableData['Geomorphological zone'] = originalGeomorphologicalZone;
    }

    if (politicalBoundary) {
        try {
            tableData['Province'] = politicalBoundary['sa_provinces'];
        } catch (e) {
        }
    }
    
    if (riverCatchments) {
        try {
            tableData['Primary Catchment'] = riverCatchments['primary_catchment_area'];
            tableData['Secondary Catchment'] = riverCatchments['secondary_catchment_area'];
            tableData['Tertiary Catchment'] = riverCatchments['tertiary_catchment_area'];
            tableData['Quaternary Catchment'] = riverCatchments['quaternary_catchment_area'];
        } catch (e) {
        }
    }

    $.each(tableData, function (key, value) {
        if(value === 'title'){
            $table.append('<tr>\n' +
                '<th class="title-row" colspan="2"> ' + key + ' </th>' +
                '</tr>');
        }else {
            $table.append('<tr>\n' +
                '<td scope="row"> ' + key + ' </td>' +
                '<td>' + value + '</td>\n' +
                '</tr>');
        }
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

function renderSourceReferences() {
    let divWrapper = $('#data-source-list');
    let dataSources = sourceReferences;
    let order = ['Reference Category', 'Author/s', 'Year', 'Title', 'Source', 'DOI/URL', 'Notes'];
    let orderedDataSources = [];
    for (var j=0; j<dataSources.length; j++) {
        orderedDataSources.push({})
        for (var i = 0; i < order.length; i++) {
            orderedDataSources[j][order[i]] = dataSources[j][order[i]];
        }
    }

    var headerDiv = $('<thead><tr></tr></thead>');
    if(orderedDataSources.length > 0) {
        var keys = Object.keys(orderedDataSources[0]);
        for (var i = 0; i < keys.length; i++) {
            headerDiv.append('<th>' + keys[i] + '</th>')
        }
    }
    divWrapper.append(headerDiv);

    var bodyDiv = $('<tbody></tbody>');
    $.each(orderedDataSources, function (index, source) {
        var itemDiv = $('<tr></tr>');
        var keys = Object.keys(source);
        var document = false;
        for(var i=0; i<keys.length; i++){
            if(source[keys[i]] === 'Published report or thesis'){
                document = true
            }

            if(keys[i] === 'DOI/URL' && document){
                itemDiv.append('<td><a href="'+ source[keys[i]] + '" target="_blank">Download</a></td>')
            }else {
                itemDiv.append('<td>' + source[keys[i]] + '</td>')
            }
        }
        bodyDiv.append(itemDiv);
    });
    divWrapper.append(bodyDiv);
}

function renderChemGraph () {
    var $chemWrapper = $('#chem-bar-chart-wrapper');
    $chemWrapper.html('');

    $.each(chemicalRecords, function (key, value) {
        var id_canvas = key + '-chem-chart';
        var canvas = '<canvas class="chem-bar-chart" id="' + id_canvas + '"></canvas>';
        $chemWrapper.append(canvas);
        try {
            var ctx = document.getElementById(id_canvas).getContext('2d');
        } catch (e) {
            return true;
        }
        var datasets = [];
        var yLabel;
        var xLabelData = [];
        $.each(value, function (idx, val) {
            var key_item = Object.keys(val)[0];
            if(key_item.toLowerCase().indexOf('max') === -1 && key_item.toLowerCase().indexOf('min') === -1){
                let unit = '';
                if (val[key_item]['name'].toLowerCase() !== 'ph') {
                    unit = ' (' + val[key_item]['unit'] + ')';
                }
                yLabel = val[key_item]['name'] + unit;
            }
            var value_data = val[key_item]['values'];
            var graph_data = [];
            for(var i=0; i<value_data.length; i++){
                graph_data.push({
                    y: value_data[i]['value'],
                    x: value_data[i]['str_date']
                });
                xLabelData.push(value_data[i]['str_date'])
            }
            datasets.push({
                label: key_item,
                data: graph_data,
                backgroundColor: '#cfdeea',
                borderColor: '#cfdeea',
                borderWidth: 2,
                fill: false
            })
        });

        xLabelData.sort(function(a, b) {
            a = new Date(a);
            b = new Date(b);
            return a < b ? -1 : a > b ? 1 : 0;
        });
        var _data = {
            labels: xLabelData,
            datasets: datasets
        };
        var options= {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            title: {
                display: false
            },
            legend: {
                display: false
            },
            scales: {
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: yLabel
                    },
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        };
        var chartConfig = {
            type: 'bar',
            data: _data,
            options: options
        };

        new Chart(ctx, chartConfig);
        options['animation'] = false;
        options['responsive'] = false;
        options['legend'] = {
            'labels': {
                'fontSize': 20,
                'boxWidth': 20
            },
        };

        chemSvgCanvases[yLabel] = C2S(600, 600);
        new Chart(chemSvgCanvases[yLabel], {
            type: 'bar',
            data: _data,
            options: options
        });
    });
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
        renderChemGraph();
        renderSourceReferences();
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
    $('.download-chart-new').click(onDownloadChartNewClicked);
    $('.download-map').click(onDownloadMapClicked);
    $('.download-chem-as-csv').click(onDownloadChemCSVClicked)
});
