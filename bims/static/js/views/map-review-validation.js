var map = new ol.Map({
        layers: [
          new ol.layer.Tile({
            source: new ol.source.OSM()
          })
        ],
        target: 'map',
        view: new ol.View({
          center: [0, 0],
          zoom: 2
        })
      });

var lastLayer = undefined;
function zoomToObject(lat, lng) {
    map.getView().setCenter(ol.proj.transform([lat, lng], 'EPSG:4326', 'EPSG:3857'));
    map.getView().setZoom(6);
    if(lastLayer !== undefined){
        map.removeLayer(lastLayer)
    }

    var iconFeatures=[];
    var iconFeature = new ol.Feature({
      geometry: new ol.geom.Point(ol.proj.transform([lat, lng], 'EPSG:4326',
      'EPSG:3857'))
    });

    var iconStyle = new ol.style.Style({
        image: new ol.style.Icon(({
            anchor: [0.5, 46],
            anchorXUnits: 'fraction',
            anchorYUnits: 'pixels',
            opacity: 0.75,
            src: '/static/img/map-marker.png'
        }))
    });

    iconFeature.setStyle(iconStyle);
    iconFeatures.push(iconFeature);

    var vectorSource = new ol.source.Vector({
      features: iconFeatures
    });

    var vectorLayer = new ol.layer.Vector({
      source: vectorSource
    });
    lastLayer = vectorLayer;
    map.addLayer(vectorLayer);
}