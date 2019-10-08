let collectionsWithAbundace = 0;
let oldLat = location_site_lat;
let oldLon = location_site_long;

let taxonAbundanceOnChange = function (e) {
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
};

let taxaIdList = [];

let taxonAutocompleteHandler = {
    source: function (request, response) {
        $.ajax({
            url: '/species-autocomplete/?term=' + encodeURIComponent(request.term) + '&exclude=' + taxaIdList.join() + '&taxonGroup=' + taxonGroupName,
            type: 'get',
            dataType: 'json',
            success: function (data) {
                response($.map(data, function (item) {
                    return {
                        label: item.species,
                        value: item.id
                    }
                }));
            }
        });
    },
    minLength: 3,
    open: function (event, ui) {
        setTimeout(function () {
            $('.ui-autocomplete').css('z-index', 99);
        }, 0);
    },
    select: function (e, u) {
        e.preventDefault();
        let $target = $(e.target);
        let $parent = $target.parent().parent();
        taxaIdList.push(u.item.value);
        $parent.html(
            '<td scope="row" class="taxon-name">' +
            u.item.label +
            '<input type="hidden" class="taxon-id" value="' + u.item.value + '">' +
            '</td>');
        $parent.append(
            '<td>' +
            '<div class="form-check">' +
            '<input class="form-check-input observed" type="checkbox"' +
            ' value="True"' +
            ' name="' + u.item.value + '-observed">' +
            ' <label class="form-check-label">' +
            ' </label>' +
            '</div>' +
            '</td>');

        let taxonAbundanceInput = $('<input type="number" min="0"' +
            ' name="' + u.item.value + '-abundance"' +
            ' class="form-control taxon-abundance"' +
            ' placeholder="0">');
        let tdTaxonAbundance = $('<td>');
        tdTaxonAbundance.append(taxonAbundanceInput);
        $parent.append(tdTaxonAbundance);
        taxonAbundanceInput.change(taxonAbundanceOnChange);

        let samplingMethodContainer = $($('#sampling-method-container').html());
        samplingMethodContainer.attr('name', u.item.value + '-sampling-method');
        let samplingMethodTd = $('<td>');
        samplingMethodTd.append(samplingMethodContainer);
        samplingMethodTd.appendTo($parent);

        let samplingEffortContainer = $($('#sampling-effort-container').html());
        $(samplingEffortContainer[0]).attr('name', u.item.value + '-sampling-effort');
        $(samplingEffortContainer[2]).attr('name', u.item.value + '-sampling-effort-type');
        let samplingEffortTd = $('<td>');
        samplingEffortTd.append(samplingEffortContainer);
        samplingEffortTd.appendTo($parent);
    }
};

$('#latitude').keyup((e) => {
    let $target = $(e.target);
    if (!document.getElementById('update-coordinate').disabled) {
        return;
    }
    if ($target.val() !== oldLat) {
        document.getElementById('update-coordinate').disabled = false;
    }
});
$('#longitude').keyup((e) => {
    let $target = $(e.target);
    if (!document.getElementById('update-coordinate').disabled) {
        return;
    }
    if ($target.val() !== oldLon) {
        document.getElementById('update-coordinate').disabled = false;
    }
});

let markerSource = new ol.source.Vector();
let map = null;
let updateCoordinateHandler = (e) => {
    let latitude = $('#latitude').val();
    let longitude = $('#longitude').val();
    let tableBody = $('#closest-site-table-body');

    if (oldLat !== latitude || oldLon !== longitude) {
    } else {
        return false;
    }

    oldLat = latitude;
    oldLon = longitude;
    document.getElementById('update-coordinate').disabled = true;
    moveMarkerOnTheMap(latitude, longitude);
    if ($('#add-new-site-container').is(":visible")) {
        return false;
    }
    $('#closest-sites-container').show();
    tableBody.html('');
    let radius = 10;
    $.ajax({
        url: '/api/get-site-by-coord/?lon=' + longitude + '&lat=' + latitude + '&radius=' + radius,
        success: function (all_data) {
            $.each(all_data, function (index, data) {
                let row = $('<tr>' +
                    '<td>' + (data['site_code'] ? data['site_code'] : '-') + '</td>' +
                    '<td>' + data['name'] + '</td>' +
                    '<td>' + (data['distance_m'] / 1000).toFixed(2) + ' km </td>' +
                    '<td> <button type="button" data-id="' + data['id'] + '" data-lat="' + data['latitude'] + '" data-lon="' + data['longitude'] + '" class="btn btn-info choose-site">' +
                    '<i class="fa fa-search" aria-hidden="true"></i></button> </td>' +
                    '</tr>');
                row.find('.choose-site').click(chooseSiteHandler);
                tableBody.append(row);
            });
        }
    });
};

$('.close-nearest-list-table').click(() => {
    $('#closest-site-table-body').html('');
    $('#closest-sites-container').hide();
});

let chooseSiteHandler = (e) => {
    e.preventDefault();
    let target = $(e.target);
    if (!target.hasClass('choose-site')) {
        target = target.parent();
    }
    let latitude = parseFloat(target.data('lat'));
    let longitude = parseFloat(target.data('lon'));
    oldLat = latitude.toString();
    oldLon = longitude.toString();
    document.getElementById('update-coordinate').disabled = true;
    let siteId = target.data('id');
    let siteCode = target.parent().parent().children().eq(0).html();
    let siteIdentifier = target.parent().parent().children().eq(1).html();
    if (siteCode !== '-') {
        siteIdentifier = siteCode
    }
    $('#site-id').val(siteId);
    $('#site-identifier').html(siteIdentifier);

    $('#latitude').val(latitude);
    $('#longitude').val(longitude);

    moveMarkerOnTheMap(latitude, longitude);
};

let moveMarkerOnTheMap = (lat, long) => {
    let locationSiteCoordinate = ol.proj.transform([
            parseFloat(long),
            parseFloat(lat)],
        'EPSG:4326',
        'EPSG:3857');
    let iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(locationSiteCoordinate),
    });
    markerSource.clear();
    markerSource.addFeature(iconFeature);
    map.getView().setCenter(locationSiteCoordinate);
};

let oldHeader = $('.header').html();
$('.add-new-site').click((e) => {
    $('#closest-sites-container').hide();
    $('#add-new-site-container').show();
    $('.header').html('Add fish data for new site');
});

$('.close-add-new-site').click((e) => {
    $('#add-new-site-container').hide();
    $('.header').html(oldHeader);
    $('#latitude').val(location_site_lat);
    $('#longitude').val(location_site_long);
    oldLat = location_site_lat;
    oldLon = location_site_long;
    $('#location-site-name').val('');
    $('#location-site-code').val('');
    $('#location-site-description').val('');
    moveMarkerOnTheMap(location_site_lat, location_site_long);
});

$(function () {
    // Get id list
    $.each($('.taxon-table-body').children(), function (index, tr) {
        let val = $(tr).children().eq(0).find('.taxon-id').val();
        if (typeof val !== 'undefined') {
            taxaIdList.push(val);
        }
    });

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
    let iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(locationSiteCoordinate),
    });
    markerSource.addFeature(iconFeature);

    map = new ol.Map({
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
            zoom: 10
        })
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

    $("#date").datepicker({
        changeMonth: true,
        changeYear: true,
        onSelect: function (dateText) {
            let $target = $(this);
            if ($target.val()) {
                $target.removeClass('error');
                $target.next().hide();
                $target.unbind();
            }
        }
    });

    let $taxonAbundance = $('.taxon-abundance');

    $taxonAbundance.keyup(function () {
        this.value = this.value.replace(/[^0-9\.]/g, '');
    });

    $taxonAbundance.change(taxonAbundanceOnChange);

    $('#owner').autocomplete({
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
        minLength: 3,
        open: function (event, ui) {
            setTimeout(function () {
                $('.ui-autocomplete').css('z-index', 99);
            }, 0);
        },
        change: function (event, ui) {
            let $ownerIdInput = $('#owner_id');
            if (ui.item) {
                $ownerIdInput.val(ui.item.value);
            } else {
                $ownerIdInput.val(' ');
                $('#owner').val('');
            }
        },
        select: function (e, u) {
            e.preventDefault();
            $('#owner').val(u.item.label);
            $('#owner_id').val(u.item.value);
        }
    });

    $('#submitBtn').click((e) => {
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
            setTimeout(function () {
                window.scrollTo(0, 0);
            }, 500);
            return;
        }
        // Get taxa list id
        let $taxaIdList = $('#taxa-id-list');
        $taxaIdList.val(taxaIdList.join());

        form.submit();
    });

    $('#add-taxon').click((e) => {
        let $findTaxonContainer = $('.find-taxon-container');
        let $findTaxonContainerClone = $findTaxonContainer.clone();
        $findTaxonContainerClone.removeClass('find-taxon-container');
        $findTaxonContainerClone.find('.taxon-input-name').autocomplete(taxonAutocompleteHandler);
        $findTaxonContainer.after($findTaxonContainerClone.show());
    });

    $('.taxon-input-name').autocomplete(taxonAutocompleteHandler);
    $('#update-coordinate').click(updateCoordinateHandler);

});