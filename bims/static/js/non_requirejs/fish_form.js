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

    let $taxonAbundance = $('.taxon-abundance');

    $taxonAbundance.keyup(function () {
        this.value = this.value.replace(/[^0-9\.]/g, '');
    });

    $taxonAbundance.change(e => {
        let value = parseInt(e.target.value);
        if (value) {
            if (value > 0) {
                $(e.target).parent().parent().find('.observed').prop('checked', true);
                return true;
            }
        }
        $(e.target).parent().parent().find('.observed').prop('checked', false);
    });

    $('#collector').autocomplete({
        source: function (request, response) {
            $.ajax({
                url: '/user-autocomplete/?term=' + encodeURIComponent(request.term),
                type: 'get',
                dataType: 'json',
                success: function (data) {
                    response($.map(data, function (item) {
                        return {
                            label: item.first_name + ' ' + item.last_name,
                            value: item.id
                        }
                    }));
                }
            });
        },
        minLength: 2,
        open: function (event, ui) {
            setTimeout(function () {
                $('.ui-autocomplete').css('z-index', 99);
            }, 0);
        },
        select: function (e, u) {
            e.preventDefault();
            $('#collector').val(u.item.label);
            $('#collector_id').val(u.item.value);
        }
    });

    $('#submitBtn').click(function () {
    });

    $('#submit').click(function () {
        $('#fish-form').submit();
    });
});