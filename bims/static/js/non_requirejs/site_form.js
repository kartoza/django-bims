let map = null;
let markerSource = null;

$(function () {
    let southAfrica = [2910598.850835484, -3326258.3640110902];
    let mapView = new ol.View({
        center: southAfrica,
        zoom: 5
    });

    map = new ol.Map({
        target: 'site-map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
        ],
        view: mapView
    });

    let biodiversityLayersOptions = {
        url: geoserverPublicUrl + 'wms',
        params: {
            LAYERS: locationSiteGeoserverLayer,
            FORMAT: 'image/png8',
            viewparams: 'where:' + defaultWMSSiteParameters
        },
        ratio: 1,
        serverType: 'geoserver'
    };
    let biodiversitySource = new ol.source.ImageWMS(biodiversityLayersOptions);
    let biodiversityTileLayer = new ol.layer.Image({
        source: biodiversitySource
    });
    map.addLayer(biodiversityTileLayer);
    $('#update-coordinate').click(updateCoordinateHandler);
    $('#update-site-code').click(updateSiteCode);
    $('#fetch-geomorphological-zone').click(fetchGeomorphologicalZone);
});

$('#latitude').keyup((e) => {
    let $target = $(e.target);
    if (!$('#latitude').val() || !$('#longitude').val()) {
        document.getElementById('update-coordinate').disabled = true;
        return;
    }
    document.getElementById('update-coordinate').disabled = false;
});
$('#longitude').keyup((e) => {
    let $target = $(e.target);
    if (!$('#latitude').val() || !$('#longitude').val()) {
        document.getElementById('update-coordinate').disabled = true;
        return;
    }
    document.getElementById('update-coordinate').disabled = false;
});

let updateSiteCode = (e) => {
    let latitude = $('#latitude').val();
    let longitude = $('#longitude').val();
    let button = $('#update-site-code');
    let siteCodeInput = $('#site_code');
    let riverInput = $('#river');
    let catchmentInput = $('#catchment_geocontext');
    let buttonLabel = button.html();

    document.getElementById('update-site-code').disabled = true;
    button.html('Generating...');
    siteCodeInput.prop('disabled', true);

    $.ajax({
        url: '/api/get-site-code/?lon=' + longitude + '&lat=' + latitude,
        success: function (data) {
            siteCodeInput.prop('disabled', false);
            siteCodeInput.val(data['site_code']);
            riverInput.val(data['river']);
            catchmentInput.val(JSON.stringify(data['catchment']));
            document.getElementById('update-site-code').disabled = false;
            button.html(buttonLabel);
        }
    });
};

let fetchGeomorphologicalZone = (e) => {
    let latitude = $('#latitude').val();
    let longitude = $('#longitude').val();
    let button = $('#fetch-geomorphological-zone');
    let geomorphologicalInput = $('#geomorphological_zone');
    let geomorphologicalGeocontextInput = $('#geomorphological_group_geocontext');
    let buttonLabel = button.html();

    button.prop('disabled', true);
    button.html('Fetching...');

    $.ajax({
        url: '/api/get-geomorphological-zone/?lon=' + longitude + '&lat=' + latitude,
        success: function (data) {
            geomorphologicalInput.val(data['geomorphological_zone']);
            geomorphologicalGeocontextInput.val(JSON.stringify(data['geomorphological_group']));
            button.prop('disabled', false);
            button.html(buttonLabel);
        }
    });
};

let updateCoordinateHandler = (e) => {
    let latitude = $('#latitude').val();
    let longitude = $('#longitude').val();
    let tableBody = $('#closest-site-table-body');

    document.getElementById('update-coordinate').disabled = true;
    $('#closest-sites-container').show();
    tableBody.html('');

    moveMarkerOnTheMap(latitude, longitude);
};

let moveMarkerOnTheMap = (lat, lon) => {
    if (!markerSource) {
        addMarkerToMap(lat, lon);
        return;
    }
    let locationSiteCoordinate = ol.proj.transform([
            parseFloat(lon),
            parseFloat(lat)],
        'EPSG:4326',
        'EPSG:3857');
    let iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(locationSiteCoordinate),
    });
    markerSource.clear();
    markerSource.addFeature(iconFeature);
    map.getView().setCenter(locationSiteCoordinate);
    map.getView().setZoom(6);
    $('#geomorphological_zone').val('');
    $('#site_code').val('');
};

let addMarkerToMap = (lat, lon) => {
    markerSource = new ol.source.Vector();
    let locationSiteCoordinate = ol.proj.transform([
            parseFloat(lon),
            parseFloat(lat)],
        'EPSG:4326',
        'EPSG:3857');
    let markerStyle = new ol.style.Style({
        image: new ol.style.Icon(({
            anchor: [0.5, 46],
            anchorXUnits: 'fraction',
            anchorYUnits: 'pixels',
            opacity: 0.75,
            src: '/static/img/map-marker.png'
        }))
    });
    let iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(locationSiteCoordinate),
    });
    markerSource.addFeature(iconFeature);
    map.addLayer(new ol.layer.Vector({
        source: markerSource,
        style: markerStyle,
    }));
    map.getView().setCenter(locationSiteCoordinate);
    map.getView().setZoom(6);
    document.getElementById('update-site-code').disabled = false;
    document.getElementById('fetch-geomorphological-zone').disabled = false;
};
