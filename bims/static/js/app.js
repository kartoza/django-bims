require.config({
    paths: {
        jquery: 'libs/jquery/jquery-3.3.1.min',
        ol: 'libs/openlayers-4.6.4/ol',
        underscore: 'libs/underscore-1.8.3/underscore-min',
        backbone: 'libs/backbone-1.3.3/backbone-min',
        bootstrap: 'libs/bootstrap-4.0.0/js/bootstrap.bundle.min',
        jqueryUi: 'libs/jquery-ui-1.12.1/jquery-ui.min',
        layerSwitcher: 'libs/ol-layerswitcher/ol-layerswitcher',
        olMapboxStyle: 'libs/ol-mapbox-style/olms',
        noUiSlider: 'libs/noUiSlider.11.1.0/nouislider',
        chartJs: 'libs/chart/Chart-2.7.2',
        'jquery-ui/ui/widget': 'libs/jquery-fileupload/vendor/jquery.ui.widget',
        'jquery.iframe-transport': 'libs/jquery-fileupload/jquery.iframe-transport',
        'jquery.fileupload': 'libs/jquery-fileupload/jquery.fileupload',
        'jquery.fileupload-process': 'libs/jquery-fileupload/jquery.fileupload-process',
        'jquery.fileupload-validate': 'libs/jquery-fileupload/jquery.fileupload-validate'
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
                'bootstrap',
                'jqueryUi',
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
    'app',
    'bootstrap',
    'jqueryUi',
    'jquery'
], function (Router, olmap, Shared, App, Bootstrap, jqueryUi, $) {
    // Display the map
    Shared.Router = new Router();

    // Start Backbone history a necessary step for bookmarkable URL's
    Backbone.history.start();

    // A $( document ).ready() block.
    $(document).ready(function () {
        $('#menu-dropdown-burger').click(function () {
            $('.dropdown-menu-left').toggle();
        });

        $('#menu-dropdown-account').click(function () {
            $('.right-nav-dropdown').toggle();
        });

        $('[data-toggle="tooltip"]').tooltip();
        $('[data-toggle="popover"]').popover();

        $.ajax({
            type: 'GET',
            url: listCollectorAPIUrl,
            dataType: 'json',
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    if(data[i]) {
                        $('#filter-collectors').append('<input type="checkbox" name="collector-value" value="' + data[i] + '"> ' + data[i] + '<br>');
                    }
                }
            }
        });

        $.ajax({
            type: 'GET',
            url: listReferenceAPIUrl,
            dataType: 'json',
            success: function (data) {
                if (data.length === 0) {
                    $('.study-reference-wrapper').hide();
                } else {
                    for (var i = 0; i < data.length; i++) {
                        if(data[i]) {
                            $('#filter-study-reference').append('<input type="checkbox" ' +
                                'name="reference-value" ' +
                                'value="' + data[i]['reference'] + '"> ' + data[i]['reference'] + '<br>');
                        }
                    }
                }
            }
        });

        $.ajax({
            type: 'GET',
            url: listCategoryAPIUrl,
            dataType: 'json',
            success: function (data) {
                var filterCategory = $('#filter-category');
                for (var i = 0; i < data.length; i++) {
                    var $wrapperDiv = $('<div></div>');
                    var $labelDiv = $('<label></label>');
                    var $inputDiv = $('<input type="checkbox"/>');

                    $wrapperDiv.addClass('ck-button');
                    $wrapperDiv.append($labelDiv);
                    $labelDiv.append($inputDiv);

                    $wrapperDiv.append($labelDiv);
                    $inputDiv.prop('id', data[i][0]);
                    $inputDiv.addClass('origins-filter-selection');
                    $inputDiv.prop('name', 'category-value');
                    $inputDiv.val(data[i][0]);
                    filterCategory.append($wrapperDiv);
                    $inputDiv.after('<span>'+data[i][1]+'</span>');
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
