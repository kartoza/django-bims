class RiskChart {
    constructor(containerId, pesticideRisk, coordinates) {
        this.containerId = containerId;
        this.pesticideRisk = pesticideRisk;
        this.coordinates = coordinates;

        this.colorMapping = {
            '': '',
            'Very Low': 'green',
            'Low': 'yellow',
            'Medium': 'blue',
            'High': 'orange',
            'Very High': 'red',
        };

        this.RISKS = ['', 'Very Low', 'Low', 'Medium', 'High', 'Very High'];
        this.RISK_KEY = {
            'mv_algae_risk': 'Algae',
            'mv_fish_risk': 'Fish',
            'mv_invert_risk': 'Invert',
        };
    }

    createChart() {
        const that = this;
        const highChartsData = Object.entries(this.pesticideRisk).map(([name, risk]) => {
            return {
                name: this.RISK_KEY[name],
                color: this.colorMapping[risk],
                y: this.RISKS.indexOf(risk),
            };
        });

        Highcharts.chart(this.containerId, {
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
                        return that.RISKS[this.value];
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
    }

    createDashboardMap() {
        // Call the 'createDashboardMap' function with the map and coordinates
        createDashboardMap(null, this.coordinates);
    }
}

const riskChart = new RiskChart('container', pesticideRisk, coordinates);
riskChart.createChart();
riskChart.createDashboardMap();
