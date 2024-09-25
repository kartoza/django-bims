function createDashboardMap(map, coordinates) {
    let scaleLineControl = new ol.control.ScaleLine();
    const baseLayer = [];
    if(bingMapKey){
        baseLayer.push(
            new ol.layer.Tile({
                source: new ol.source.BingMaps({
                    key: bingMapKey,
                    imagerySet: 'AerialWithLabels'
                })
            })
        )
    }
    else {
        baseLayer.push(
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })
        )
    }
    map = new ol.Map({
        controls: ol.control.defaults.defaults().extend([
            scaleLineControl
        ]),
        layers: baseLayer,
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
    if (coordinates) {
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
    }
    map.getView().setZoom(10);

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
    return map;
}
