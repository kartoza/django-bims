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
function zoomToObject(lat, lng) {
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
}

function showDetail(pk) {
    $.ajax({
        url: '/api/get-bio-object/',
        data: {'pk': pk},
        success: function (data) {
            const $detailModal = $('#detailModal');
            $detailModal.find('.modal-body').html('<table></table>');
            for (var key in data) {
                $detailModal.find('.modal-body').append(`<tr><td class="capitalize">${key.replace(/_/g, ' ')}</td><td>${data[key]}</td></tr>`);
            }
            $detailModal.modal();
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

$(document).ready(function () {
    $('input[type="date"]').datepicker(
        {
            dateFormat: 'yyyy-mm-dd',
            changeMonth: true,
            changeYear: true
        }
    ).attr('type', 'text');

    updateSelectedFilter(customUrl)
});

function validateObject(pk) {
    const modal = $('#confirmValidateModal');
    modal.modal('show');
    modal.data('id', pk);
}

$('#validateBtn').click(function () {
    const modal = $('#confirmValidateModal');
    const id = modal.data('id');
    $.ajax({
        url: validateUrl,
        data: {'pk': id},
        success: function () {
            location.reload()
        }
    })
});

function rejectObject(pk) {
    const modal = $('#confirmRejectModal');
    modal.find('.rejection-message').val('');
    modal.modal('show');
    modal.data('id', pk);
}

$('#rejectBtn').click(function () {
    const modal = $('#confirmRejectModal');
    const id = modal.data('id');
    const rejectionMessage = modal.find('.rejection-message');
    $.ajax({
        url: rejectUrl,
        data: {
            'pk': id,
            'rejection_message': rejectionMessage.val()
        },
        success: function () {
            location.reload()
        }
    })
});

function deleteObject(pk) {
    const modal = $('#confirmDeleteModal');
    modal.modal('show');
    modal.data('id', pk);
}

$('#deleteBtn').click(function () {
    const modal = $('#confirmDeleteModal');
    const id = modal.data('id');
    let url = deleteDataUrl;
    url = url.replace('0', id);
    url += '?next=' + currentUrl;
    $.ajax({
        url: url,
        type: 'POST',
        success: function () {
            location.reload()
        }
    })
});

function sendEmailValidation(pk) {
    $.ajax({
        url: '/api/send-email-validation/',
        data: {'pk': pk},
        success: function () {
            $('#message-success').show().html('Validation notification is sent.');
            setTimeout(location.reload(), 3000)
        }
    });
}

function dynamicInputFilter(that) {
    const $inputOptions = $('.input-options');
    const $btnGo = $('#btn-go');
    const $btnReset = $('#btn-reset');
    $btnReset.hide();
    $inputOptions.hide().val('');
    $inputOptions.parent().hide();
    if (that.value) {
        const $input = $('.' + that.value);
        $input.parent().show();
        $input.show();
        $btnGo.show();
    }
}

$('input[name=filter_result]').click(function () {

    var selected_filter = $('#filter-select').val();
    var url = pageUrl;
    if(selected_filter === 'collection_date'){
        var filter_date_to = $('input[name=date_to]').val();
        var filter_date_from = $('input[name=date_from]').val();
        url += '?';
        if(filter_date_from !== '' && filter_date_to !== '') {
            url += 'date_from=' + filter_date_from + '&date_to=' + filter_date_to;
        }else if(filter_date_from !== ''){
            url += 'date_from=' + filter_date_from
        }else {
            url += 'date_to=' + filter_date_to
        }
    }else if(selected_filter !== ''){
        var filter_value = $('input[name=' + selected_filter + ']').val();
        url += '?'+ selected_filter +'=' + filter_value
    }

    window.location.href = url;
});

function updateSelectedFilter(customUrl) {
    var filter_options = ['original_species_name', 'date_to', 'date_from', 'owner'];
    var value;
    for (var key in filter_options) {
        var selected_filter = filter_options[key];
        if(selected_filter !== 'date_to' && selected_filter !=='date_from') {
            if (customUrl.indexOf(selected_filter) > -1) {
                $('#filter-select').val(selected_filter);
                $('.' + selected_filter).show();
                value = customUrl.split(selected_filter + '=')[1];
                $('input[name=' + selected_filter + ']').val(value);
            }
        }else {
            if (customUrl.indexOf(selected_filter) > -1) {
                $('#filter-select').val('collection_date');
                $('.collection_date').show();
                value = customUrl.split(selected_filter + '=')[1];
                value = value.split('&')[0];
                $('input[name=' + selected_filter + ']').val(value);
            }
        }
    }
}

if(window.location.href.split('?')[1]){
    if(!window.location.href.split('?')[1].includes("page")){
        const $btnReset = $('#btn-reset');
        $btnReset.show();
        $btnReset.click( function (){
        window.location.href = window.location.href.split('?')[0];
    });
    }

}

