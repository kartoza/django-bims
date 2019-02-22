let ecoregionChartPlotsLabel = {};

let ecologicalChartOptions = {
    hover: {
        intersect: true
    },
    legend: {
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
            }
        }],
        xAxes: [{
            type: 'linear',
            position: 'bottom',
            display: true,
            ticks: {
                suggestedMin: 0,
                suggestedMax: 200
            }
        }]
    },
    tooltips: {
        callbacks: {
            title: function (tooltipItems, data) {
                if (!ecoregionChartPlotsLabel) {
                    return;
                }
                let label = '-';
                let dotIdentifier = tooltipItems[0]['xLabel'] + '-' + parseFloat(tooltipItems[0]['yLabel']).toFixed(2);
                if (ecoregionChartPlotsLabel.hasOwnProperty(dotIdentifier)) {
                    label = ecoregionChartPlotsLabel[dotIdentifier];
                }
                return label;
            },
            label: function (tooltipItem, data) {
                let label = data.datasets[tooltipItem.datasetIndex].label || '';
                if (label) {
                    label += ': ';
                }
                label += tooltipItem.xLabel + ', ' + tooltipItem.yLabel;
                return label;
            }
        }
    }
};

function hexToRgb(hex) {
    let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function createBoundaryDataset(x, y) {
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

function createEcologicalChart(
    canvas,
    ecologicalCategoryData,
    scatterPlotData,
    chartTitle = '',
    sass_key = 'sass', aspt_key = 'aspt', color_key = 'color', category_key = 'ec_category') {

    let dataSets = [];
    let scatterDatasets = [];

    $.each(ecologicalCategoryData, (index, ecologicalData) => {
        dataSets.unshift(createBoundaryDataset(
            ecologicalData[sass_key],
            ecologicalData[aspt_key],
            ecologicalData[color_key])
        );
        let ecologicalColor = ecologicalData[color_key];
        let ecologicalCategoryName = ecologicalData[category_key];
        if (!scatterDatasets.hasOwnProperty(ecologicalCategoryName)) {
            scatterDatasets[ecologicalCategoryName] = createEcologicalScatterDataset(
                ecologicalColor,
                ecologicalCategoryName,
                []
            );
        }
    });

    $.each(scatterPlotData, function (index, plotData) {
        let asptScore = plotData[aspt_key];
        let sassScore = plotData[sass_key];
        let plotLabel = '-';
        if (plotData.hasOwnProperty('label')) {
            plotLabel = plotData['label'];
        }

        let scatterData = null;
        $.each(ecologicalCategoryData, function (index, ecologicalData) {
            let ecologicalCategoryName = ecologicalData[category_key];
            if (sassScore > ecologicalData[sass_key] || asptScore > ecologicalData[aspt_key]) {
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
            if (!ecoregionChartPlotsLabel.hasOwnProperty(dotIdentifier)) {
                ecoregionChartPlotsLabel[dotIdentifier] = '';
            }
            if (ecoregionChartPlotsLabel[dotIdentifier]) {
                ecoregionChartPlotsLabel[dotIdentifier] += ', ';
            }
            ecoregionChartPlotsLabel[dotIdentifier] += plotLabel;
            scatterDatasets[scatterData['label']]['data'].push({
                'x': scatterData['x'],
                'y': scatterData['y']
            });
            scatterData = null;
        }
    });

    for (let key in scatterDatasets) {
        dataSets.unshift(scatterDatasets[key]);
    }

    new Chart(canvas, {
        type: "bar",
        labels: [],
        data: {
            datasets: dataSets
        },
        options: ecologicalChartOptions
    });
    canvas.parent().append('<div class="chart-bottom-title">' + chartTitle + '</div>');
}
