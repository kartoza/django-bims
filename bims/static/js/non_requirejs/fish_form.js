$(function () {
    let collectionsWithAbundace = 0;
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
                collectionsWithAbundace += 1;
                return true;
            }
        }
        $(e.target).parent().parent().find('.observed').prop('checked', false);
        collectionsWithAbundace -= 1;
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

    $('#submitBtn').click((e) => {
        e.preventDefault();
    });

    let form = $('#fish-form');
    $('#submit').click((event) => {
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
        if (collectionsWithAbundace === 0) {
            isError = true;
            alertMessage = 'You must at least add one collection data';
        } else {
            let alertDiv = $('.alert-danger');
            alertDiv.html('');
            alertDiv.hide();
        }
        if (alertMessage) {
            let alertDiv = $('.alert-danger');
            alertDiv.html(alertMessage);
            alertDiv.show();
        }
        if (isError) {
            event.preventDefault();
            event.stopPropagation();
            $('#confirm-submit').modal('hide');
            return;
        }
        form.submit();
    });


});