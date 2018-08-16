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
                    $('#filter-category').append('<input type="checkbox" name="category-value" value="' + data[i] + '">&nbsp;' + data[i] + '<br>');
                }
            }
        });
        $.ajax({
            type: 'GET',
            url: listBoundaryAPIUrl,
            dataType: 'json',
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    $('#filter-catchment-area').append('<input type="checkbox" name="boundary-value" value="' + data[i]['id'] + '">&nbsp;' + data[i]['name'] + '<br>');
                }
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
    });
});
