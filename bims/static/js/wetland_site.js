let wetlandData = null;
let wmsSource = null;
let wmsLayer = null;
let wmsLayerName = 'kartoza:nwm6_beta_v3_20230714';

if (window.wetlandData) {
  wetlandData = window.wetlandData;
}

updateCoordinate = function (zoomToMap = true) {
  try {
    let latitude = parseFloat($('#latitude').val());
    let longitude = parseFloat($('#longitude').val());
    if (!latitude || !longitude) {
      return false;
    }
    let _coordinates = ol.proj.transform([longitude, latitude], 'EPSG:4326', 'EPSG:3857');
    mapClicked(_coordinates);
  } catch (e) {
    return false;
  }
};

const getFeature = (layerSource, coordinates, renderResult) => {
  let _coordinates = ol.proj.transform(coordinates, 'EPSG:3857', 'EPSG:4326');
  if (markerSource) {
    markerSource.clear();
  }
  $('#latitude').val('');
  $('#longitude').val('');
  $('#hydrogeomorphic_type').val('');

  return new Promise((resolve, reject) => {
    $.ajax({
      type: 'POST',
      url: '/get_feature/',
      data: {
        'layerSource': layerSource
      },
      timeout: 5000,
      success: function (result) {
        const data = result['feature_data'];
        let objectData = {};
        if (data.constructor === Object) {
          objectData = data;
        } else {
          try {
            objectData = JSON.parse(data);
          } catch (e) {
            console.log(e);
            reject(e);
            return;
          }
        }
        let features = objectData['features'];
        if (features.length > 0) {
          const feature = features[0];
          const bbox = feature['bbox'];

          map.getView().fit(bbox, {size: map.getSize()});
          if (renderResult) {
            $('#latitude').val(_coordinates[1]);
            $('#longitude').val(_coordinates[0]);

            $('#fetch-river-name').attr('disabled', false);
            $('#fetch-geomorphological-zone').attr('disabled', false);
            $('#wetland-site-code').attr('disabled', false);

            $('#site_code').val('');

            let olFeature = new ol.format.GeoJSON().readFeatures(feature);

            const format = new ol.format.GeoJSON();
            const featureObj = format.readFeature(feature, {
              dataProjection: 'EPSG:3857',
              featureProjection: 'EPSG:3857'
            })
            const geometry = featureObj.getGeometry();
            geometry.transform('EPSG:3857', 'EPSG:4326');

            const convertedGeojsonStr = format.writeFeature(featureObj, {
              dataProjection: 'EPSG:4326',
              featureProjection: 'EPSG:4326'
            });

            $('#site-geometry').val(convertedGeojsonStr);
            // vectorLayer.getSource().clear()
            // vectorLayer.getSource().addFeatures(olFeature);
            wetlandData = feature['properties'];
            $('#additional-data').val(JSON.stringify(wetlandData));
            $('#river_name').val(wetlandData['name'] ? wetlandData['name'] : '');
            $('#hydrogeomorphic_type').val(wetlandData['hgm_type'] ? wetlandData['hgm_type'] : '');

            moveMarkerOnTheMap(_coordinates[1], _coordinates[0], false);
          }
        }
        resolve(features);
      },
      error: function (err) {
        if(err.status === 0){
          alert("The site is unreachable at the moment.");
        } else {
          alert("An error occurred: " + err.statusText);
        }
        reject(err);
      }
    });
  });
};


let mapClicked = (coordinate) => {
  if (!wmsLayer) return;

  let view = map.getView();
  let layerSource = wmsLayer.getSource().getGetFeatureInfoUrl(
      coordinate,
      view.getResolution(),
      view.getProjection(),
      {'INFO_FORMAT': 'application/json'}
  );
  layerSource += '&QUERY_LAYERS=' + wmsLayerName;
  const zoomLevel = map.getView().getZoom();
  $('#map-loading').css('display', 'flex');
  $('#update-coordinate').attr('disabled', true);
  getFeature(layerSource, coordinate,zoomLevel > 10).then(function(features) {
    if (features.length > 0 && zoomLevel <= 10) {
      let bbox = features[0]['bbox'];
      let centroidX = (bbox[0] + bbox[2]) / 2;
      let centroidY = (bbox[1] + bbox[3]) / 2;
      let point = [centroidX, centroidY];

      layerSource = wmsLayer.getSource().getGetFeatureInfoUrl(
          point,
          view.getResolution(),
          view.getProjection(),
          {'INFO_FORMAT': 'application/json'}
      );
      layerSource += '&QUERY_LAYERS=' + wmsLayerName;
      getFeature(layerSource, coordinate, true).then(function (f) {
        $('#map-loading').hide();
        $('#update-coordinate').attr('disabled', false);
      })
    } else {
      $('#map-loading').hide();
      $('#update-coordinate').attr('disabled', false);
    }
  }).catch(function(error) {
    // handle any errors
  });
}

let mapReady = (map) => {

  // Add wetland layer
  let geoserverWms = 'https://maps.kartoza.com/geoserver/wms'

   // Create a new WMS source
  wmsSource = new ol.source.TileWMS({
    url: geoserverWms,
    params: {'LAYERS': wmsLayerName},
    serverType: 'geoserver',
  });

  // Create a new tile layer with the WMS source
  wmsLayer = new ol.layer.Tile({
    source: wmsSource
  });

  let vectorLayer = new ol.layer.Vector({
    source: new ol.source.Vector(),
    style: new ol.style.Style({
      fill: new ol.style.Fill({
        color: 'yellow'
      }),
      stroke: new ol.style.Stroke({
        color: '#black',
        width: 2
      })
    })
  });

  // Add the WMS layer to the map
  map.addLayer(wmsLayer);
  map.addLayer(vectorLayer);

  map.un('click', mapOnClicked);

  map.on('click', function(e) {
    mapClicked(e.coordinate);
  });
}

let wetlandSiteCodeButton =  $('#wetland-site-code');

wetlandSiteCodeButton.click(function () {
  if (!wetlandData) return false

  let siteCodeInput = $('#site_code');
  wetlandSiteCodeButton.attr('disabled', true);
  wetlandSiteCodeButton.html('Generating...');

  let siteCode = wetlandData['quaternary'].substring(0, 4);

  let wetlandName = $('#wetland_name').val() !== '-' ? $('#wetland_name').val() : '';
  if (!wetlandName) {
    wetlandName = $('#user_wetland_name').val()
  }

  if (wetlandName) {
    wetlandName = '-' + wetlandName.substring(0, 4);
  }

  siteCode += wetlandName;

  let url = '/api/get-site-code/?user_site_code=' + siteCode;

  $.ajax({
    url: url,
    success: function (data) {
      siteCodeInput.val(data['site_code']);
    }
  }).done(function () {
    wetlandSiteCodeButton.attr('disabled', false);
    wetlandSiteCodeButton.html('Generate site code');
  });
});
