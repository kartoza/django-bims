let dashboardMap = null;
let wmsUrl = 'https://maps.kartoza.com/geoserver/wms';
let pesticideLayers = {};
const riskModules = {
    'Algae': 'mv_algae_risk',
    'Fish': 'mv_fish_risk',
    'Invert': 'mv_invert_risk',
}
const IGNORED_VALUE = ['fid', 'geom', 'QUATERNARY', 'Toxic Unit Score', 'risk_category']

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
    }

    createChart() {
        const that = this;
        const highChartsData = Object.entries(this.pesticideRisk).map(([name, risk]) => {
            return {
                name: Object.keys(riskModules).find(key => riskModules[key] === name),
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

    createDashboardMap(map = null) {
        // Call the 'createDashboardMap' function with the map and coordinates
        dashboardMap = createDashboardMap(map, this.coordinates);
        for (const key of Object.keys(riskModules)) {
            pesticideLayers[key] = new ol.layer.Tile({
                opacity: 0.1,
                source: new ol.source.TileWMS({
                    url: wmsUrl,
                    params: {
                        'LAYERS': 'kartoza:' + riskModules[key],
                        'TILED': true
                    },
                    serverType: 'geoserver'
                })
            })
            dashboardMap.addLayer(pesticideLayers[key]);
        }
    }
}

const riskChart = new RiskChart('container', pesticideRisk, coordinates);
riskChart.createChart();
riskChart.createDashboardMap();

class PesticideTable {
    constructor() {
    }

    getFeatureData(layer, _coordinates, callback) {
        const view = dashboardMap.getView();
        let layerSource = layer.getSource().getGetFeatureInfoUrl(
            _coordinates,
            view.getResolution(),
            view.getProjection(),
        );
        $.ajax({
            type: 'POST',
            url: '/get_feature/',
            data: {
                'layerSource': layerSource,
            },
            success: function (result) {
                const featureData = result.feature_data.split('\n');
                let values = [];
                featureData.forEach(line => {
                    const [key, value] = line.split(' = ');

                    if (!IGNORED_VALUE.includes(key) && !isNaN(parseFloat(value))) {
                        values.push({key, value: parseFloat(value)});
                    }
                });
                values.sort((a, b) => b.value - a.value);
                callback(values);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.error(xhr)
                callback(null);
            }
        })
    }

    generatesTable() {
        let _coordinates = [];
        dashboardMap.getLayers().forEach(function(layer) {
            if (layer instanceof ol.layer.Vector) {
                _coordinates = layer.getSource().getFeatures()[0].getGeometry().getCoordinates();
                return false;
            }
        });
        for (const key of Object.keys(pesticideLayers)) {
            const layer = pesticideLayers[key];
            this.getFeatureData(layer, _coordinates, (values) => {
                if (values) {
                    const top10 = values.slice(0, 10);
                    $('.top-10-pesticides').append(
                        `<tr>
                            <th colspan="2">${key}</th>
                        </tr>`
                    )
                    for (const pesticide of top10) {
                        $('.top-10-pesticides').append(
                            `<tr>
                                <td>${pesticide.key}</td>
                                <td>${pesticide.value}</td>
                            </tr>`
                        )
                    }
                }
            });
        }
    }
}

const pesticideTable = new PesticideTable();
pesticideTable.generatesTable();
