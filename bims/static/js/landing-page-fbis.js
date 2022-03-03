$(document).ready(function () {
    $.ajax({
        url: '/api/module-summary/',
        dataType: 'json',
        success: function (data) {
            var fishData = null;
            if (data.hasOwnProperty('fish')) {
                fishData = data['fish'];
            }
            createFishCharts(fishData);
            if (data.hasOwnProperty('invert')) {
                createInvertCharts(data['invert']);
            }
            if (data.hasOwnProperty('algae')) {
                createAlgaeChart(data['algae']);
            }
            if (data.hasOwnProperty('odonate')) {
                createOdonateChart(data['odonate'])
            }
            if (data.hasOwnProperty('anura')) {
                createAnuraChart(data['anura'])
            }
        }
    });
    $('[data-toggle="tooltip"]').tooltip()
});

function createOdonateChart(odonateData) {
    if (!odonateData) {
        return;
    }
    $('#chart-odonate').parent().empty().append('<canvas id="chart-odonate" width="150px" height="150px"></canvas>');
    let endemismData = {};
    let labels = [];
    let data = [];
    if (odonateData.hasOwnProperty('endemism')) {
        for (let key in odonateData['endemism']) {
            endemismData[key] = odonateData['endemism'][key]
            data.push(odonateData['endemism'][key])
            labels.push(key)
        }
    }

    $('#odonate-total-records').html(odonateData['total'].toLocaleString());
    $('#odonate-total-sites').html(odonateData['total_site'].toLocaleString());
    const chartContainer = document.getElementById("chart-odonate");
    const chartDataset = {
        labels: labels,
        datasets: [{
            data: data,
            backgroundColor: [
                '#a13447',
                '#00a99d',
                '#e0d43f'
            ],
            borderWidth: 1
        }]
    };
    createDonutGraph(chartContainer, chartDataset)
}

function createAnuraChart(anuraData) {
    if (!anuraData) {
        return;
    }
    $('#chart-anura').parent().empty().append('<canvas id="chart-anura" width="150px" height="150px"></canvas>');
    var native = 0;
    var non_native = 0;
    var lc = 0;
    var nt = 0;
    var vu = 0;
    var en = 0;
    let dd = 0;
    let ne = 0;
    let ce = 0;
    var totalSite = 0;
    var totalSpecies = 0;

    if (anuraData.hasOwnProperty('Least concern')) {
        lc += anuraData['Least concern'];
    }
    if (anuraData.hasOwnProperty('Near threatened')) {
        nt += anuraData['Near threatened'];
    }
    if (anuraData.hasOwnProperty('Vulnerable')) {
        vu += anuraData['Vulnerable'];
    }
    if (anuraData.hasOwnProperty('Endangered')) {
        en += anuraData['Endangered'];
    }
    if (anuraData.hasOwnProperty('Not evaluated')) {
        ne += anuraData['Not evaluated'];
    }
    if (anuraData.hasOwnProperty('Critically endangered')) {
        ce += anuraData['Critically endangered'];
    }
    if (anuraData.hasOwnProperty('total')) {
        totalSpecies += anuraData['total'];
    }
    if (anuraData.hasOwnProperty('total_site')) {
        totalSite += anuraData['total_site'];
    }
    if (anuraData.hasOwnProperty('Data Deficient')) {
        dd += anuraData['Data Deficient'];
    }

    $('#anura-total-records').html(totalSpecies.toLocaleString());
    $('#anura-total-sites').html(totalSite.toLocaleString());

    var anuraContainer = document.getElementById("chart-anura");
    var anuraChartDataset = {
        labels: ["Data Deficient", "Not evaluated", "Least concern", "Near threatened", "Vulnerable", "Endangered", "Critically endangered"],
        datasets: [{
            data: [dd, ne, lc, nt, vu, en, ce],
            backgroundColor: [
                '#808080',
                '#818181',
                '#65c25e',
                '#b8b75f',
                '#ff8f36',
                '#fe5328',
                '#810a27',
            ],
            borderWidth: 1
        }]
    };
    createDonutGraph(anuraContainer, anuraChartDataset)
}


function createFishCharts(fishData) {
    if (!fishData) {
        return;
    }
    $('#chart-fish').parent().empty().append('<canvas id="chart-fish" width="150px" height="150px"></canvas>');
    var native = 0;
    var non_native = 0;
    var lc = 0;
    var nt = 0;
    var vu = 0;
    var en = 0;
    let dd = 0;
    let ne = 0;
    let ce = 0;
    var totalSite = 0;
    var totalSpecies = 0;

    if (fishData.hasOwnProperty('Least concern')) {
        lc += fishData['Least concern'];
    }
    if (fishData.hasOwnProperty('Near threatened')) {
        nt += fishData['Near threatened'];
    }
    if (fishData.hasOwnProperty('Vulnerable')) {
        vu += fishData['Vulnerable'];
    }
    if (fishData.hasOwnProperty('Endangered')) {
        en += fishData['Endangered'];
    }
    if (fishData.hasOwnProperty('Not evaluated')) {
        ne += fishData['Not evaluated'];
    }
    if (fishData.hasOwnProperty('Critically endangered')) {
        ce += fishData['Critically endangered'];
    }
    if (fishData.hasOwnProperty('total')) {
        totalSpecies += fishData['total'];
    }
    if (fishData.hasOwnProperty('total_site')) {
        totalSite += fishData['total_site'];
    }
    if (fishData.hasOwnProperty('Data Deficient')) {
        dd += fishData['Data Deficient'];
    }

    $('#fish-total-records').html(totalSpecies.toLocaleString());
    $('#fish-total-sites').html(totalSite.toLocaleString());

    var fishContainer = document.getElementById("chart-fish");
    var fishChartDataset = {
        labels: ["Data Deficient", "Not evaluated", "Least concern", "Near threatened", "Vulnerable", "Endangered", "Critically endangered"],
        datasets: [{
            data: [dd, ne, lc, nt, vu, en, ce],
            backgroundColor: [
                '#808080',
                '#818181',
                '#65c25e',
                '#b8b75f',
                '#ff8f36',
                '#fe5328',
                '#810a27',
            ],
            borderWidth: 1
        }]
    };
    createDonutGraph(fishContainer, fishChartDataset)
}

function createInvertCharts(invertData) {
     $('#chart-invert').parent().empty().append('<canvas id="chart-invert" width="150px" height="150px"></canvas>');
    let invertContainer = document.getElementById("chart-invert");
    let totalInvert = 0;
    let totalSite = 0;
    let totalSass = 0;
    if (invertData.hasOwnProperty('total')) {
        totalInvert += invertData['total'];
    }
    if (invertData.hasOwnProperty('total_site')) {
        totalSite += invertData['total_site'];
    }
    if (invertData.hasOwnProperty('total_sass')) {
        totalSass += invertData['total_sass'];
    }
    $('#invert-total-records').html(totalInvert);
    $('#invert-total-sites').html(totalSite.toLocaleString());
    $('#invert-total-sass').html(totalSass.toLocaleString());
    let labels = [];
    let backgroundColors = [];
    let chartData = [];
    $.each(invertData['ecological_data'], function (index, ecologicalData) {
        labels.push(ecologicalData['value']);
        backgroundColors.push(ecologicalData['color']);
        chartData.push(ecologicalData['count']);
    });
    let invertChartDataset = {
        labels: labels,
        datasets: [{
            data: chartData,
            backgroundColor: backgroundColors,
            borderWidth: 1
        }]
    };
    createDonutGraph(invertContainer, invertChartDataset);
}

function createAlgaeChart(algaeData) {
    if (!algaeData) {
        return;
    }
    $('#chart-algae').parent().empty().append('<canvas id="chart-algae" width="150px" height="150px"></canvas>');
    let algaeContainer = document.getElementById("chart-algae");
    $('#algae-total-records').html(algaeData['total'].toLocaleString());
    $('#algae-total-sites').html(algaeData['total_site'].toLocaleString());
    let algaeChartDataset = {
        labels: ['Algae'],
        datasets: [{
            data: [algaeData['total']],
            backgroundColor: ['#18A090'],
            borderWidth: 1
        }]
    };
    createDonutGraph(algaeContainer, algaeChartDataset);
}

function createDonutGraph(container, data) {
    var donutChart = new Chart(container, {
        type: 'doughnut',
        data: data,
        options: {
            cutoutPercentage: 70,
            legend: {
                display: false
            }
        }
    });
}