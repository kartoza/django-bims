require.config({
    paths: {
        jquery: 'libs/jquery/jquery-3.3.1.min',
        bootstrap: 'libs/bootstrap-4.0.0/js/bootstrap.bundle.min',
        ol: 'libs/openlayers-4.6.4/ol',
        underscore: 'libs/underscore-1.8.3/underscore-min',
        backbone: 'libs/backbone-1.3.3/backbone-min',
        jqueryUi: 'libs/jquery-ui-1.12.1/jquery-ui.min',
        layerSwitcher: 'libs/ol-layerswitcher/ol-layerswitcher',
        olMapboxStyle: 'libs/ol-mapbox-style/olms',
        noUiSlider: 'libs/noUiSlider.11.1.0/nouislider',
        chartJs: 'libs/chart/Chart-2.7.2'
    },
    shim: {
        ol: {
            exports: ['ol']
        },
        underscore: {
            exports: '_'
        },
        backbone: {
            deps: [
                'underscore',
                'jquery'
            ],
            exports: 'Backbone'
        },
        app: {
            deps: ['backbone']
        },
        layerSwitcher: {
            deps: ['ol'],
            exports: 'LayerSwitcher'
        },
        olMapboxStyle: {
            deps: ['ol'],
            exports: 'OlMapboxStyle'
        }
    }
});

require([
    'router',
    'views/olmap',
    'shared',
    'app'
], function (Router, olmap, Shared, App) {
    // Display the map
    Shared.Router = new Router();

    // Start Backbone history a necessary step for bookmarkable URL's
    Backbone.history.start();

    // A $( document ).ready() block.
    $(document).ready(function () {

        $('[data-toggle="tooltip"]').tooltip();

        $.ajax({
            type: 'GET',
            url: listCollectorAPIUrl,
            dataType: 'json',
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    $('#filter-collectors').append('<input type="checkbox" name="collector-value" value="' + data[i] + '"> ' + data[i] + '<br>');
                }
            }
        });
        $.ajax({
            type: 'GET',
            url: listCategoryAPIUrl,
            dataType: 'json',
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    $('#filter-category').append('<input type="checkbox" name="category-value" value="' + data[i][0] + '">&nbsp;' + data[i][1] + '<br>');
                }
            }
        });
        $.ajax({
            type: 'GET',
            url: listBoundaryAPIUrl,
            dataType: 'json',
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    var $wrapper = $('#filter-catchment-area');
                    if (data[i]['top_level_boundary']) {
                        if ($('#boundary-' + data[i]['top_level_boundary']).length > 0) {
                            $wrapper = $('#boundary-' + data[i]['top_level_boundary']);
                        }
                    }
                    $wrapper.append(
                        '<div>' +
                        '<input type="checkbox" name="boundary-value" value="' + data[i]['id'] + '" data-level="' + data[i]['type__level'] + '">&nbsp;' + data[i]['name'] +
                        '<div id="boundary-' + data[i]['id'] + '" style="padding-left: 15px"></div>' +
                        '</div> ');
                }
                $('#filter-catchment-area input').click(function () {
                    var child = $('#boundary-' + $(this).val());
                    var level = $(this).data('level');
                    if ($(this).is(':checked')) {
                        $(child).find('input:checkbox:not(:checked)[data-level="' + (level + 1) + '"]').click();
                    } else {
                        $(child).find('input:checkbox:checked[data-level="' + (level + 1) + '"]').click();
                    }
                });
            }
        });

        $('.try-again-button').click(function () {
            Shared.Dispatcher.trigger('map:reloadXHR', this.features)
        });
        $('.mouse-position button').click(function () {
            if ($('.mouse-position').hasClass('active')) {
                $('.mouse-position').removeClass('active');
                $('#mouse-position-wrapper').hide();
            } else {
                $('.mouse-position').addClass('active');
                $('#mouse-position-wrapper').show();
            }
        });
        $(".date-filter").datepicker({dateFormat: 'yy-mm-dd'});
        $('.close-info-popup').click(function () {
            if($('input[name=dont-show-info]').is(':checked')){
                $.ajax({
                    type: 'GET',
                    url: hideBimsInfoUrl,
                    success: function () {
                        $('#general-info-modal').fadeOut();
                    }
                })
            }
            $('#general-info-modal').fadeOut();
        })
    });
});
