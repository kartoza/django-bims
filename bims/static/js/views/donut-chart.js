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