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

// Custom control
window.app = {};
var app = window.app;

app.RotateNorthControl = function(opt_options) {

var options = opt_options || {};

var button = document.createElement('button');
button.innerHTML = '<i class="fa fa-pencil"></i>';
var element = document.createElement('div');

var this_ = this;
var enableDisableEdit = function() {
  if(!$('.enable-edit-map').hasClass('selected')){
      addInteractions();
      $('.enable-edit-map').addClass('selected');
      element.title = 'Disable edit';
  }else {
      $('.enable-edit-map').removeClass('selected');
      removeInteraction();
      element.title = 'Enable edit';
  }
};

button.addEventListener('click', enableDisableEdit, false);
button.addEventListener('touchstart', enableDisableEdit, false);

element.className = 'enable-edit-map ol-unselectable ol-control';
element.appendChild(button);
element.title = 'Enable edit';

ol.control.Control.call(this, {
  element: element,
  target: options.target
});

};
ol.inherits(app.RotateNorthControl, ol.control.Control);


var basemap_layers = basemaps();
var baselayers = new ol.layer.Group({
        'title': 'Base maps',
        layers: basemap_layers
    });

var map = new ol.Map({
    layers: [baselayers, vector],
    target: 'map',
    view: new ol.View({
        center: [0, -23],
        zoom: 2
    }),
    controls: ol.control.defaults({
        attributionOptions: {
            collapsible: false
        }
    }).extend([
        new app.RotateNorthControl()
    ])
});

var layerSwitcher = new LayerSwitcher();
map.addControl(layerSwitcher);

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

    draw.on('drawend', function (e) {
        if(typeSelect.value === 'Point'){
            setTimeout(function () {
                var features = source.getFeatures();
                var coordinates;
                features.forEach(function(feature) {
                   coordinates = feature.getGeometry().getCoordinates();
                   coordinates = ol.proj.transform(coordinates, 'EPSG:3857','EPSG:4326');
                   $('#custom-lat').val(coordinates[0]);
                   $('#custom-long').val(coordinates[1]);
                });
            }, 100)
        }
    })

}

function removeInteraction() {
    map.removeInteraction(draw);
    map.removeInteraction(snap);
    $('.enable-edit-map').removeClass('selected');
}

/**
* Handle change event.
*/
typeSelect.onchange = function() {
    removeInteraction();
    source.clear();
    if(typeSelect.value !== 'Point'){
        $('#coordinates-input-wrapper').hide();
    }else {
        $('#coordinates-input-wrapper').show();
    }
};

function basemaps() {
    var baseSourceLayers = [];

    // TOPOSHEET MAP
    var toposheet = new ol.layer.Tile({
        title: 'Topography',
        source: new ol.source.XYZ({
            attributions: ['&copy; National Geo-spatial Information (NGI) contributors', 'Toposheets'],
            url: 'https://htonl.dev.openstreetmap.org/ngi-tiles/tiles/50k/{z}/{x}/{-y}.png'
        })
    });

    // NGI MAP
    var ngiMap = new ol.layer.Tile({
        title: 'Aerial photography',
        source: new ol.source.XYZ({
            attributions: ['<a href="http://www.ngi.gov.za/">CD:NGI Aerial</a>'],
            url: 'http://aerial.openstreetmap.org.za/ngi-aerial/{z}/{x}/{y}.jpg'
        })
    });

    // OSM MAPSURFER ROADS - Make default
    var mapSurfer = new ol.layer.Tile({
        title: 'OpenStreetMap',
        source: new ol.source.XYZ({
            attributions: ['&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'],
            url: 'https://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}'
        })
    });

    // add bing
    if (bingMapKey) {
        var bingMap = new ol.layer.Tile({
            title: 'Bing Satellite Hybrid',
            source: new ol.source.BingMaps({
                key: bingMapKey,
                imagerySet: 'AerialWithLabels'
            })
        });
        baseSourceLayers.push(bingMap);
    }

    baseSourceLayers.push(ngiMap);
    baseSourceLayers.push(mapSurfer);
    baseSourceLayers.push(toposheet);

    $.each(baseSourceLayers, function (index, layer) {
        layer.set('type', 'base');
        layer.set('visible', true);
        layer.set('preload', Infinity);
    });

    return baseSourceLayers
}
