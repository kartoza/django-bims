let map = null;

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

function renderWaterTemperatureChart(){
    // let temperature_data = JSON.parse(data)
    // let data_chart = []
    // for(let i in temperature_data){
    //     let item = []
    //     item[0] = temperature_data[i]['date'].split(' ')[0];
    //     item[1] = temperature_data[i]['mean'];
    //     data_chart.push(item)
    // }
    let url = '/api/thermal-data/?site-id='+ siteId
    fetch(url).then((response => {
        return response.json()
        })
    ).then((data =>{
        const chart = new Highcharts.Chart({
        chart: {
            renderTo: 'water-temperature',
            type: 'spline',

        },
        title: {
            text: '',
        },
        xAxis: {
            type: 'datetime',
            title: {
                text: 'Date'
            }
        },
        yAxis: {
            title: {
                text: 'Water Temperature (°C)'
            }
        },

        legend: {
            layout: 'horizontal',
            enabled: true,
            verticalAlign: 'top'
        },
        series: [
            {
                name: '95%_low',
                data: data['95%_low'],
                color: '#7f7f7f'
            },
            {
                name: '95%_up',
                data: data['95%_up'],
                color: '#7f7f7f'
            },
            {
                name: 'L95%_1SD',
                data: data['L95%_1SD'],
                color: '#bfbfbf'

            },
            {
                name: 'U95%_1SD',
                data: data['U95%_1SD'],
                color: '#bfbfbf'

            },
            {
                name: 'L95%_2SD',
                data: data['L95%_2SD'],
                color: '#bfbfbf'

            },
            {
                name: 'U95%_2SD',
                data: data['U95%_2SD'],
                color: '#bfbfbf'

            },
            {
                name: 'Mean_7',
                data: data['mean_7'],
                color: '#000000'
            },
            {
                name: 'Min_7',
                data: data['min_7'],
                color: '#0070c0'
            },
            {
                name: 'Max_7',
                data: data['max_7'],
                color: '#ff0000'
            },

        ]
    });
            return chart

    }))
}


$(function () {
    drawMap();
    renderWaterTemperatureChart()
});