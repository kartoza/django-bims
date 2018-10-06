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
    'jquery'
], function (Router, olmap, Shared, App, $) {
    // Display the map
    Shared.Router = new Router();

    // Start Backbone history a necessary step for bookmarkable URL's
    Backbone.history.start();

    // A $( document ).ready() block.
    $(document).ready(function () {

        // Set top margin for layer switcher panel
        var mapControlPanelHeight = $('.map-control-panel').height();
        $('.layer-switcher').css('top', (mapControlPanelHeight + 91) + 'px');
        $('.download-control-panel').css('top', (mapControlPanelHeight + 46) + 'px');

        $('#menu-dropdown-burger').click(function () {
            $('.dropdown-menu-left').toggle();
        });

        $('#menu-dropdown-account').click(function () {
            $('.right-nav-dropdown').toggle();
        });

        $('[data-toggle="tooltip"]').tooltip();

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
