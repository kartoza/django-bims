$(function () {
    let locationSiteCoordinate = ol.proj.transform([
            parseFloat(location_site_long),
            parseFloat(location_site_lat)],
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
    let markerSource = new ol.source.Vector();
    let iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(locationSiteCoordinate),
    });
    markerSource.addFeature(iconFeature);

    let map = new ol.Map({
        target: 'fish-map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
            new ol.layer.Vector({
                source: markerSource,
                style: markerStyle,
            }),
        ],
        view: new ol.View({
            center: locationSiteCoordinate,
            zoom: 11
        })
    });

    $("#date").datepicker({
        changeMonth: true,
        changeYear: true
    });
});