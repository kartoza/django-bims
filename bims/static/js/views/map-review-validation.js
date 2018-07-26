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
var popup = new ol.Overlay({
    element: document.getElementById('popup'),
    positioning: 'bottom-center',
    offset: [0, -50]
});
map.addOverlay(popup);

var lastLayer = undefined;
function zoomToObject(lat, lng, pk) {
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

    $.ajax({
        url: '/api/get-bio-object/',
        data: {'pk': pk},
        success: function (data) {
            var keywords = ['id', 'owner', 'original_species_name', 'category', 'collection_date', 'collector', 'notes'];
            $('#popup').html('');
            $('#popup').html('<table></table>');
            for(var key in data){
                if(keywords.indexOf(key) > -1) {
                    $('#popup').append('<tr><td>' + key + '</td><td>' + data[key] + '</td></tr>')
                }
            }
            popup.setPosition(ol.proj.transform([lat, lng], 'EPSG:4326', 'EPSG:3857'));
        }
    });
}

map.on('singleclick', function(e) {
    var features = map.getFeaturesAtPixel(e.pixel);
    if(features) {
        var coordinate = features[0].getGeometry().getCoordinates();
        popup.setPosition(coordinate);
    }else {
        popup.setPosition(undefined)
    }
  });