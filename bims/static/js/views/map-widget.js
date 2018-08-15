var raster = new ol.layer.Tile({
    source: new ol.source.OSM()
});

var source = new ol.source.Vector();
var vector = new ol.layer.Vector({
    source: source,
    style: new ol.style.Style({
      fill: new ol.style.Fill({
        color: 'rgba(255, 255, 255, 0.2)'
      }),
      stroke: new ol.style.Stroke({
        color: '#ffcc33',
        width: 2
      }),
      image: new ol.style.Circle({
        radius: 7,
        fill: new ol.style.Fill({
          color: '#ffcc33'
        })
      })
    })
});

var map = new ol.Map({
    layers: [raster, vector],
    target: 'map',
    view: new ol.View({
        center: [0, -23],
        zoom: 2
    })
});

var draw, snap;
var typeSelect = document.getElementById('type');

function addInteractions() {
    draw = new ol.interaction.Draw({
        source: source,
        type: typeSelect.value
    });

    snap = new ol.interaction.Snap({source: source});

    map.addInteraction(draw);
    map.addInteraction(snap);

    draw.on('drawstart', function (e) {
        source.clear();
    });
}

/**
* Handle change event.
*/
typeSelect.onchange = function() {
    map.removeInteraction(draw);
    map.removeInteraction(snap);
    addInteractions();
    source.clear();
};

addInteractions();
