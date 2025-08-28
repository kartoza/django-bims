let wetlandData = null;
let wmsSource = null;
let wmsLayer = null;
let wmsLayerName = 'bims:nwm6_beta_v3_20230714';
let currentCoordinate = null;

let wetlandSiteCodeButton =  $('#wetland-site-code');
let fetchWetlandNameButton = $('#fetch-wetland-name');
let fetchHydrogeomorphicBtn = $('#fetch-hydrogeomorphic-type')

if (window.wetlandData) {
  wetlandData = window.wetlandData;
}

updateCurrentCoordinate = function () {
  try {
    let latitude = parseFloat($('#latitude').val());
    let longitude = parseFloat($('#longitude').val());
    if (!latitude || !longitude) {
      return false;
    }
    let _coordinates = ol.proj.transform([longitude, latitude], 'EPSG:4326', 'EPSG:3857');
    currentCoordinate = _coordinates;
  } catch (e) {
    return false;
  }
}

updateCoordinate = function (zoomToMap = true) {
  updateCurrentCoordinate();
  mapClicked(currentCoordinate);
};

const getFeature = (layerSource, coordinates, renderResult) => {
  let _coordinates = ol.proj.transform(coordinates, 'EPSG:3857', 'EPSG:4326');

  $('#map-loading').css('display', 'flex');
  $('#update-coordinate').attr('disabled', true);
  wetlandSiteCodeButton.attr('disabled', true);
  fetchWetlandNameButton.attr('disabled', true);
  fetchHydrogeomorphicBtn.attr('disabled', true);

  return new Promise((resolve, reject) => {
    $.ajax({
      type: 'POST',
      url: '/get_feature/',
      data: {
        'layerSource': layerSource
      },
      timeout: 5000,
      success: function (result) {

        $('#map-loading').hide();
        $('#update-coordinate').attr('disabled', false);
        fetchWetlandNameButton.attr('disabled', false);
        fetchHydrogeomorphicBtn.attr('disabled', false);
        wetlandSiteCodeButton.attr('disabled', false);

        const data = result['feature_data'];
        let objectData = {};
        if (data.constructor === Object) {
          objectData = data;
        } else {
          try {
            objectData = JSON.parse(data);
          } catch (e) {
            reject(e);
            return;
          }
        }
        let features = objectData['features'];
        if (features.length > 0) {
          const feature = features[0];
          const bbox = feature['bbox'];

          // map.getView().fit(bbox, {size: map.getSize()});
          if (renderResult) {
            $('#wetland-site-code').attr('disabled', false);

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
          }
        }
        resolve(features);
      },
      error: function (err) {
        reject(err);
      }
    });
  });
};


let mapClicked = (coordinate) => {
  if (!wmsLayer) return;
  currentCoordinate = coordinate;
  let tableBody = $('#closest-site-table-body');
  let loadingIndicator = document.getElementById('loading-indicator');

  loadingIndicator.style.display = 'block';
  loadingIndicator.textContent = 'Checking nearby sites...';

  document.getElementById('update-coordinate').disabled = true;
  $('#closest-sites-container').show();
  tableBody.html('');

  let _coordinates = ol.proj.transform(coordinate, 'EPSG:3857', 'EPSG:4326');
  moveMarkerOnTheMap(_coordinates[1], _coordinates[0], false);

  let radius = 0.5;
  let url =  '/api/get-site-by-coord/?lon=' + _coordinates[0] + '&lat=' + _coordinates[1] + '&radius=' + radius;
  if (ecosystemType) {
      url += '&ecosystem=' + ecosystemType;
  }
  $.ajax({
      url: url,
      success: function (all_data) {
          loadingIndicator.style.display = 'none';
          if (all_data.length > 0) {
              let nearestSite = null;
              if (siteId) {
                  let site_id = parseInt(siteId);
                  $.each(all_data, function (index, site_data) {
                  if (site_data['id'] !== site_id) {
                          nearestSite = site_data;
                          return false;
                      }
                  });
              } else {
                  nearestSite = all_data[0];
              }

              if (nearestSite) {
                  let modal = $("#site-modal");
                  let nearestSiteName = '';
                  if (nearestSite['site_code']) {
                      nearestSiteName = nearestSite['site_code'];
                  } else {
                      nearestSiteName = nearestSite['name'];
                  }
                  modal.find('#nearest-site-name').html(nearestSiteName);
                  modal.find('#existing-site-button').attr('onClick', 'location.href="/location-site-form/update/?id=' + nearestSite['id'] + '"');
                  modal.modal('show');
              }
          }
      },
      error: function (err) {
          loadingIndicator.style.display = 'none';
          console.log(err);
      }
  });

  wetlandSiteCodeButton.attr('disabled', false);

  $('#latitude').val(_coordinates[1]);
  $('#longitude').val(_coordinates[0]);

  fetchWetlandNameButton.attr('disabled', false);
  fetchHydrogeomorphicBtn.attr('disabled', false);
}

let fetchWetlandData = () => {
  if (!currentCoordinate) return;
  let coordinate = currentCoordinate;
  let view = map.getView();
  let layerSource = wmsLayer.getSource().getFeatureInfoUrl(
      coordinate,
      view.getResolution(),
      view.getProjection(),
      {'INFO_FORMAT': 'application/json'}
  );
  layerSource += '&QUERY_LAYERS=' + wmsLayerName;
  const zoomLevel = map.getView().getZoom();
  return getFeature(layerSource, coordinate,true)
}

let mapReady = (map) => {

  // Add wetland layer
  let geoserverWms = 'https://geoserver.bims.kartoza.com/geoserver/wms'

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

wetlandSiteCodeButton.click(function () {
  let siteCodeInput = $('#site_code');
  wetlandSiteCodeButton.attr('disabled', true);
  wetlandSiteCodeButton.html('Generating...');

  let latitude = parseFloat($('#latitude').val());
  let longitude = parseFloat($('#longitude').val());

  let url = `/api/get-site-code/?ecosystem_type=Wetland&user_wetland_name=${$('#river_name').val() || $('#user_river_name').val()}&lat=${latitude}&lon=${longitude}`;

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

fetchWetlandNameButton.click(function () {
  fetchWetlandData().then((features) => {
    try {
      $('#river_name').val(features[0]['properties']['name']);
    } catch (e) {
      $('#river_name').val('');
    }
    if (!$('#river_name').val()) {
      alert('Please add User Wetland Name.')
    }
  })
})

fetchHydrogeomorphicBtn.click(function () {
  fetchWetlandData().then((features) => {
    try {
      $('#hydrogeomorphic_type').val(features[0]['properties']['hgm_type']);
    } catch (e) {
      $('#hydrogeomorphic_type').val('');
    }
  })
})
