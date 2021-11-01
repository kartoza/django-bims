const baseLayer = []
let markerSource = new ol.source.Vector();
let markerStyle = new ol.style.Style({
    image: new ol.style.Icon(({
        anchor: [0.5, 46],
        anchorXUnits: 'fraction',
        anchorYUnits: 'pixels',
        opacity: 0.75,
        src: '/static/img/map-marker.png'
    }))
});

if (bingKey) {
    baseLayer.push(
        new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: bingKey,
                imagerySet: 'AerialWithLabels'
            })
        })
    )
} else {
    baseLayer.push(
        new ol.layer.Tile({
            source: new ol.source.OSM()
        })
    )
}
baseLayer.push(
    new ol.layer.Vector({
        source: markerSource,
        style: markerStyle,
    }),
)
let locationSiteCoordinate = ol.proj.transform([
        parseFloat(location_site_long),
        parseFloat(location_site_lat)],
    'EPSG:4326',
    'EPSG:3857');
let map = new ol.Map({
    target: 'map',
    layers: baseLayer,
    view: new ol.View({
        center: locationSiteCoordinate,
        zoom: 10
    })
});
let iconFeature = new ol.Feature({
    geometry: new ol.geom.Point(locationSiteCoordinate),
});
markerSource.addFeature(iconFeature);

const processWaterData = (formData) => {
    $.ajax({
        url: `/upload-water-temperature/`,
        headers: {"X-CSRFToken": csrfToken},
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function (data) {
            $('html, body').animate({
                scrollTop: $(".dashboard-title").offset().top
            }, 1);
            document.getElementById('upload').disabled = false;
            document.getElementById('upload').value = 'Upload';

            if (data['status'] == 'failed') {
                let alertDiv = $('.alert-danger');
                alertDiv.html('Errors : <br>')
                for (let i = 0; i < data['message'].length; i++) {
                    alertDiv.append(`${data['message'][i]}<br>`)
                }
                alertDiv.show();
                document.getElementById('upload').disabled = false;
                document.getElementById('upload').value = 'Upload';
            }
            if (data['status'] == 'success') {
                let alertDiv = $('.alert-success');
                alertDiv.html(data['message']);
                alertDiv.show();
            }
        }
    });
}

$('#upload').click((event) => {
    let required_inputs = $('input,textarea,select').filter('[required]:visible');
    let isError = false;
    let alertMessage = '';
    $.each(required_inputs, (index, input) => {
        let $input = $(input);
        if (!$input.val()) {
            isError = true;
            $input.addClass('error');
            $input.keyup((e) => {
                let $target = $(e.target);
                if ($target.val()) {
                    $target.removeClass('error');
                    $target.next().hide();
                    $target.unbind();
                }
            });
            $input.next().show();
        } else {
            $input.unbind();
        }
    });
    if (alertMessage) {
        let alertDiv = $('.alert-danger');
        alertDiv.html(alertMessage);
        alertDiv.show();
    }
    if (isError) {
        event.preventDefault();
        event.stopPropagation();
        setTimeout(function () {
            window.scrollTo(0, 0);
        }, 500);
        return;
    }

    const formData = new FormData();
    formData.append("water_file", $('#water_file')[0].files[0])
    formData.append("site-id", $('#site-id').val())
    formData.append("owner_id", $('#owner_id').val())
    formData.append("interval", $('#logging-interval').val())
    formData.append("format", $('#format-date').val())
    formData.append("start_time", $('#start-time').val())
    formData.append("end_time", $('#end-time').val())

    document.getElementById('upload').disabled = true;
    document.getElementById('upload').value = 'Checking data...';

    $.ajax({
        url: `/validate-water-temperature/`,
        headers: {"X-CSRFToken": csrfToken},
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function (data) {
            $('html, body').animate({
                scrollTop: $(".dashboard-title").offset().top
            }, 1);
            if (data['status'] == 'failed') {
                let alertDiv = $('.alert-danger');
                alertDiv.html('Errors : <br>')
                for (let i = 0; i < data['message'].length; i++) {
                    alertDiv.append(`${data['message'][i]}<br>`)
                }
                alertDiv.show();
                document.getElementById('upload').disabled = false;
                document.getElementById('upload').value = 'Upload';
            }
            if (data['status'] == 'success') {
                document.getElementById('upload').value = 'Processing data...';
                formData.append("upload_session_id", data['upload_session_id']);
                processWaterData(formData);
            }
        }
    });
});