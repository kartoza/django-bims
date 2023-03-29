const colorMapping = {
    '': '',
    'Very Low': 'green',
    'Low': 'yellow',
    'Medium': 'blue',
    'High': 'orange',
    'Very High': 'red',
};

const RISKS = ['', 'Very Low', 'Low', 'Medium', 'High', 'Very High']
const RISK_KEY = {
    'mv_algae_risk': 'Algae',
    'mv_fish_risk': 'Fish',
    'mv_invert_risk': 'Invert'
}


const highChartsData = Object.entries(pesticideRisk).map(([name, risk]) => {
    return {
        name: RISK_KEY[name],
        color: colorMapping[risk],
        y: RISKS.indexOf(risk),
    };
});

console.log(highChartsData)

Highcharts.chart('container', {
    chart: {
        type: 'column',
    },
    title: {
        text: '',
    },
    xAxis: {
        categories: ['Algae', 'Fish', 'Invert'],
    },
    yAxis: {
        min: 0,
        max: 6,
        tickInterval: 1,
        labels: {
            // Custom formatter function for yAxis labels
            formatter: function () {
                return RISKS[this.value]
            },
        },
        title: {
            text: '',
        },
    },
    series: [
        {
            showInLegend: false,
            data: highChartsData,
        },
    ],
    tooltip: {
        enabled: false,
    },
    plotOptions: {
        series: {
            groupPadding: 0,
            pointPadding: 0.1,
        },
    },
});

let map = null;
$(function () {
    createDashboardMap(map, coordinates);
    $('.download-map').click(function () {
        map.once('postrender', function (event) {
            showDownloadPopup('IMAGE', 'Map', function () {
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
            })
        });
        map.renderSync();
    })
});