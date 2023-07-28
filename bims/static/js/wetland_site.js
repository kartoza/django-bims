

let mapReady = (map) => {

  // Add wetland layer
  let geoserverWms = 'https://maps.kartoza.com/geoserver/wms'
  let wmsLayerName = 'kartoza:nwm6_beta_v3_20230714';

   // Create a new WMS source
  let wmsSource = new ol.source.TileWMS({
    url: geoserverWms,
    params: {'LAYERS': wmsLayerName},
    serverType: 'geoserver',
  });

  // Create a new tile layer with the WMS source
  let wmsLayer = new ol.layer.Tile({
    source: wmsSource
  });
  let view = map.getView();

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

  const getFeature = (layerSource, renderResult) => {
    return new Promise((resolve, reject) => {
      $.ajax({
        type: 'POST',
        url: '/get_feature/',
        data: {
          'layerSource': layerSource
        },
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
              let olFeature = new ol.format.GeoJSON().readFeatures(feature);
              vectorLayer.getSource().clear()
              vectorLayer.getSource().addFeatures(olFeature);
            }
          }
          resolve(features);
        },
        error: function (err) {
          console.log(err);
          reject(err);
        }
      });
    });
  };


  map.on('click', function(e) {
    let layerSource = wmsLayer.getSource().getGetFeatureInfoUrl(
      e.coordinate,
      view.getResolution(),
      view.getProjection(),
      {'INFO_FORMAT': 'application/json'}
    );
    layerSource += '&QUERY_LAYERS=' + wmsLayerName;
    const zoomLevel = map.getView().getZoom();
    console.log(zoomLevel)
    getFeature(layerSource, zoomLevel > 10).then(function(features) {
        if (features.length > 0 && zoomLevel <= 10) {
          let bbox = features[0]['bbox'];
          let centroidX = (bbox[0] + bbox[2]) / 2;
          let centroidY = (bbox[1] + bbox[3]) / 2;
          let point = [centroidX, centroidY];
          console.log(point)

          let pointFeature = new ol.Feature({
            geometry: new ol.geom.Point(point)
          });

          let pointSource = new ol.source.Vector({
            features: [pointFeature]
          });

          let pointLayer = new ol.layer.Vector({
            source: pointSource,
            style: new ol.style.Style({
              image: new ol.style.Circle({
                radius: 7,
                fill: new ol.style.Fill({color: 'black'}),
                stroke: new ol.style.Stroke({
                  color: [255, 0, 0], width: 2
                })
              })
            })
          });

          map.addLayer(pointLayer);

          layerSource = wmsLayer.getSource().getGetFeatureInfoUrl(
            point,
            view.getResolution(),
            view.getProjection(),
            {'INFO_FORMAT': 'application/json'}
          );
          layerSource += '&QUERY_LAYERS=' + wmsLayerName;
          getFeature(layerSource, true)
        }
    }).catch(function(error) {
        // handle any errors
    });
  });
}