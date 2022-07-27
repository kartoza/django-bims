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

function createSummaryChart(data){

    if(!data){
        return;
    }
    let bColor;
    let labels = [];
    let dataChart = [];


    if(data.hasOwnProperty('conservation-status')){
        let lc = 0;
        let nt = 0;
        let vu = 0;
        let en = 0;
        let dd = 0;
        let ne = 0;
        let ce = 0;

        let anuraData = data['conservation-status'];
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
        if (anuraData.hasOwnProperty('Data Deficient')) {
            dd += anuraData['Data Deficient'];
        }

        labels = ["Data Deficient", "Not evaluated", "Least concern", "Near threatened", "Vulnerable", "Endangered", "Critically endangered"],
        dataChart = [dd, ne, lc, nt, vu, en, ce];
        bColor = [
                '#D7CD47',
                '#39B2A3',
                '#17766B',
                '#2C495A',
                '#525351',
                '#8D2641',
                '#641f30',
            ];
    }
    else if(data.hasOwnProperty('endemism')){

         for (let key in data['endemism']) {
             dataChart.push(data['endemism'][key]);
             labels.push(key)
         }
         bColor = [
                    '#a13447',
                    '#00a99d',
                    '#e0d43f'
                ];
    }

    else if (data.hasOwnProperty('division')) {
        $.each(data['division'], function (index, divisionData) {
            if (divisionData['taxonomy__additional_data__Division'] == null) {
                labels.push('Unknown');
            } else {
                labels.push(divisionData['taxonomy__additional_data__Division']);
            }
            dataChart.push(divisionData['count']);
        });
        bColor = [
            '#8D2641', '#641f30',
            '#E6E188', '#D7CD47',
            '#9D9739', '#525351',
            '#618295', '#2C495A',
            '#39B2A3', '#17766B',
            '#859FAC', '#1E2F38'
        ];


    }
    else if (data.hasOwnProperty('origin')) {

        for (let key in data['origin']) {
            dataChart.push(data['origin'][key]);
            labels.push(key)
        }
        bColor = [
            '#a13447',
            '#e0d43f'
        ];
    }else {
        $.each(data['ecological_data'], function (index, ecologicalData) {
            labels.push(ecologicalData['value']);
            dataChart.push(ecologicalData['count']);
        });
        bColor = [
            '#641f30',
            '#8D2641',
            '#D7CD47',
            '#17766B',
            '#39B2A3'
        ];
    }

    return {
            labels: labels,
            datasets: [{
                data: dataChart,
                backgroundColor: bColor,
                borderWidth: 1
            }]
        };


}

function createOdonateChart(odonateData) {

    $('#chart-odonate').parent().empty().append('<canvas id="chart-odonate" width="150px" height="150px"></canvas>');
    $('#odonate-total-records').html(odonateData['total'].toLocaleString());
    $('#odonate-total-sites').html(odonateData['total_site'].toLocaleString());
    const chartContainer = document.getElementById("chart-odonate");
    const chartDataset = createSummaryChart(odonateData)
    createDonutGraph(chartContainer, chartDataset)
}

function createAnuraChart(anuraData) {

    $('#chart-anura').parent().empty().append('<canvas id="chart-anura" width="150px" height="150px"></canvas>');
    let totalSite = 0;
    let totalSpecies = 0;

    if (anuraData.hasOwnProperty('total')) {
        totalSpecies += anuraData['total'];
    }
    if (anuraData.hasOwnProperty('total_site')) {
        totalSite += anuraData['total_site'];
    }

    $('#anura-total-records').html(totalSpecies.toLocaleString());
    $('#anura-total-sites').html(totalSite.toLocaleString());

    const anuraContainer = document.getElementById("chart-anura");
    const anuraChartDataset = createSummaryChart(anuraData);
    createDonutGraph(anuraContainer, anuraChartDataset)
}


function createFishCharts(fishData) {

    $('#chart-fish').parent().empty().append('<canvas id="chart-fish" width="150px" height="150px"></canvas>');
    var totalSite = 0;
    var totalSpecies = 0;

    if (fishData.hasOwnProperty('total')) {
        totalSpecies += fishData['total'];
    }
    if (fishData.hasOwnProperty('total_site')) {
        totalSite += fishData['total_site'];
    }

    $('#fish-total-records').html(totalSpecies.toLocaleString());
    $('#fish-total-sites').html(totalSite.toLocaleString());

    var fishContainer = document.getElementById("chart-fish");
    var fishChartDataset = createSummaryChart(fishData);
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

    createDonutGraph(invertContainer, createSummaryChart(invertData));
}

function createAlgaeChart(algaeData) {

    $('#chart-algae').parent().empty().append('<canvas id="chart-algae" width="150px" height="150px"></canvas>');
    let algaeContainer = document.getElementById("chart-algae");
    $('#algae-total-records').html(algaeData['total'].toLocaleString());
    $('#algae-total-sites').html(algaeData['total_site'].toLocaleString());

    createDonutGraph(algaeContainer, createSummaryChart(algaeData));
}

function createDonutGraph(container, data) {
    const donutChart = new Chart(container, {
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