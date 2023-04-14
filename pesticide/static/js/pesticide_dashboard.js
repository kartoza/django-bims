let dashboardMap = null;
let wmsUrl = 'https://maps.kartoza.com/geoserver/wms';
let pesticideLayers = {
    'Fish': '',
    'Invert': '',
    'Algae': '',
}
const riskModules = {
    'Fish': 'mv_fish_risk',
    'Invert': 'mv_invert_risk',
    'Algae': 'mv_algae_risk',
}
const IGNORED_VALUE = ['fid', 'geom', 'QUATERNARY', 'Toxic Unit Score', 'risk_category']
let QUATERNARY = '';
let riskCategories = {
    'mv_fish_risk': '',
    'mv_invert_risk': '',
    'mv_algae_risk': '',
};

function downloadPesticideData(url, filename, extension = 'csv') {
    showDownloadPopup('CSV', filename, async function () {
        try {
            const response = await fetch(url);
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename + '.' + extension;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                console.error('Error fetching CSV data:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('Error fetching CSV data:', error);
        }
    }, true)
}

class RiskChart {
    constructor(containerId, pesticideRisk, coordinates) {
        this.containerId = containerId;
        this.pesticideRisk = pesticideRisk;
        this.coordinates = coordinates;

        this.colorMapping = {
            '': '#d3d3d3',
            'Very Low': '#80bfab',
            'Low': '#ffffbf',
            'Medium': '#fec980',
            'High': '#f07c4a',
            'Very High': '#e31a1c',
        };
        this.RISKS = ['', 'Very Low', 'Low', 'Medium', 'High', 'Very High'];

        $('.download-generic-pesticide-risk-indicator').click(() => {
            const filename = 'Generic Pesticide Risk Indicator';
            downloadPesticideData('/static/GenericRI.xlsx', filename, 'xlsx');
        })

        $('.download-specific-pesticide-risk-indicator').click(() => {
            const filename = 'Specific Pesticide Risk Indicator';
            downloadPesticideData('/static/SpecificRI.xlsx', filename, 'xlsx');
        })
    }

    downloadPesticideByQuaternary() {
        const filename = 'Pesticide Use (' + QUATERNARY + ')';
        downloadPesticideData('/pesticide-by-quaternary/' + QUATERNARY + '/', filename);
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

    getFeatureData(module, layer, _coordinates, callback) {
        const view = dashboardMap.getView();
        let that = this;
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
                $('.loading-data').hide();
                const featureData = result.feature_data.split('\n');
                let values = [];
                featureData.forEach(line => {
                    const [key, value] = line.split(' = ');
                    if (key === 'QUATERNARY' && !QUATERNARY) {
                        // Show download quaternary button
                        QUATERNARY = value;
                        $('.download-pesticide-by-quaternary').attr('disabled', false).click(that.downloadPesticideByQuaternary);
                    }
                    if (key === 'risk_category') {
                        riskCategories[riskModules[module]] = value;
                    }
                    if (!IGNORED_VALUE.includes(key) && !isNaN(parseFloat(value))) {
                        values.push({key, value: parseFloat(value)});
                    }
                });
                values.sort((a, b) => b.value - a.value);
                if (Object.keys(riskCategories).length === 3) {
                    that.pesticideRisk = riskCategories;
                    that.createChart();
                }
                callback(values);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                $('.loading-data').hide();
                console.error(xhr)
                callback(null);
            }
        })
    }

    generatesTable() {
        let _coordinates = [];
        dashboardMap.getLayers().forEach(function(layer) {
            if (layer instanceof ol.layer.Vector) {
                _coordinates = ol.proj.transform(coordinates, 'EPSG:4326', 'EPSG:3857');
                return false;
            }
        });
        for (const key of Object.keys(pesticideLayers)) {
            const layer = pesticideLayers[key];
            this.getFeatureData(key, layer, _coordinates, (values) => {
                if (values) {
                    const top10 = values.slice(0, 10);
                    top10.sort((a, b) => a.value - b.value);
                    const tableClass = $(`.top-10-pesticides .${key}-pesticide`)
                    for (const pesticide of top10) {
                        tableClass.after(
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

const pesticideTable = new RiskChart('container', pesticideRisk, coordinates);
pesticideTable.createDashboardMap();
pesticideTable.generatesTable();
