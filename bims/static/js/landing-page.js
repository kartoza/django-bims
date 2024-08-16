function searchOnMap(event) {
    event.preventDefault();
    if (event.keyCode === 13) {
        location.href = '/map/#search/' + $('#search-on-map').val();
    }
}

function generateDoughnutChart(container, data) {
    var myChart = new Chart(container, {
        type: 'doughnut',
        data: data,
        options: {
            legend: {
                display: false
             },
            cutoutPercentage: 85,
            maintainAspectRatio: false
        }
    });
}

document.addEventListener('DOMContentLoaded', function (event) {

    var summaryData = JSON.parse(summaries);

    $.each(summaryData, function (className, classData) {
        var labels = [];
        var category_data= [];
        var background_color = [];

        $.each(classData, function (key, value) {
            if(key !== 'total') {
                category_data.push(value);
                if(key === 'indigenous') {
                    background_color.push('#ddd14e');
                    labels.push('Native');
                } else if(key === 'alien') {
                    background_color.push('#649b49');
                    labels.push('Non-Native');
                } else {
                    background_color.push('#3e5033');
                    labels.push('Translocated');
                }
            }
        });
        var config = {
            labels: labels,
            datasets: [{
                data: category_data,
                backgroundColor: background_color,
                borderColor: background_color,
                borderWidth: 1
            }]
        };
        var chartContainer = document.getElementById("chart-"+className);
        generateDoughnutChart(chartContainer, config);
    });
});

function createSummaryChart(data){
    if(!data){
        return;
    }
    let bColor;
    let labels = [];
    let dataChart = [];
    if(data.hasOwnProperty('conservation-status')){
        labels = Object.keys(data['conservation-status']['chart_data'])
        dataChart = Object.values(data['conservation-status']['chart_data']);
        bColor = data['conservation-status']['colors'];
    }
    else if(data.hasOwnProperty('endemism')){
        for (let key in data['endemism']) {
            dataChart.push(data['endemism'][key]);
            labels.push(key)
        }
        bColor = [
            '#a13447',
            '#641f30',
            '#E6E188',
            '#e0d43f',
            '#00a99d',
            '#17766B',
            '#2C495A'
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
    } else {
        let ecologicalCategory = {
            'A': 'Natural (N)',
            'B': 'Good (G)',
            'C': 'Fair (F)',
            'D': 'Poor (P)',
            'E': ['(S/CM)', 'Seriously/Critically', 'Modified']
        }
        $.each(data['ecological_data'], function (index, ecologicalData) {
            labels.push(ecologicalCategory[ecologicalData['value']]);
            dataChart.push(ecologicalData['count']);
        });
        bColor = [
            '#0000ff',
            '#008000',
            '#ffa500',
            '#ff0000',
            '#800080'
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

