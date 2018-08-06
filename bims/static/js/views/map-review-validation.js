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
function zoomToObject(lat, lng, pk) {
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

    $.ajax({
        url: '/api/get-bio-object/',
        data: {'pk': pk},
        success: function (data) {
            var keywords = ['id', 'owner', 'original_species_name', 'category', 'collection_date', 'collector', 'notes'];
            $('#popup').html('');
            $('#popup').html('<table></table>');
            for(var key in data){
                if(keywords.indexOf(key) > -1) {
                    $('#popup').append('<tr><td>' + key + '</td><td>' + data[key] + '</td></tr>')
                }
            }
            popup.setPosition(ol.proj.transform([lat, lng], 'EPSG:4326', 'EPSG:3857'));
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
    $.ajax({
        url: validateUrl,
        data: {'pk': pk},
        success: function () {
            location.reload()
        }
    });
}

function sendEmailValidation(pk) {
    $.ajax({
        url: '/api/send-email-validation/',
        data: {'pk': pk},
        success: function () {
            alert('Validation notification sent!')
        }
    });
}

function dynamicInputFilter(that) {
    $('.input-options').hide().val('');
    $('.' + that.value).show();
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
