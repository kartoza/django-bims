let collectionsWithAbundace = 0;
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

let taxonAutocompleteHandler = {
    source: function (request, response) {
        $.ajax({
            url: '/species-autocomplete/?term=' + encodeURIComponent(request.term),
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
        $parent.html(
            '<td scope="row" class="taxon-name">' +
            u.item.label +
            '<input type="hidden" value="' + u.item.value + '">' +
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

        let samplingMethodContainer = $parent.next().find('.sampling-method-container').clone();
        samplingMethodContainer.children().attr('name', u.item.value + '-sampling-method');
        samplingMethodContainer.appendTo($parent);

        let samplingEffortContainer = $parent.next().find('.sampling-effort-container').clone();
        $(samplingEffortContainer.children()[0]).attr('name', u.item.value + '-sampling-effort');
        $(samplingEffortContainer.children()[1]).attr('name', u.item.value + '-sampling-effort-type');
        samplingEffortContainer.appendTo($parent);
    }
};

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
        minLength: 3,
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

});