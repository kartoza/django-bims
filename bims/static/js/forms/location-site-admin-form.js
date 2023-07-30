(function ($) {
    $(document).ready(function () {
        var $geometryInput = $('[class*="geometry_"]');
        var init = true;
        $geometryInput.hide();
        function resetAllGeometries() {
            geodjango_geometry_point.clearFeatures();
            geodjango_geometry_line.clearFeatures();
            geodjango_geometry_polygon.clearFeatures();
            geodjango_geometry_multipolygon.clearFeatures();
        }

        $('#id_location_type').change(function () {
            if (!init) {
                resetAllGeometries();
            }
            init = false;
            if ($(this).val()) {
                $.get("/api/location-type/" + $(this).val() + '/allowed-geometry/', function (data) {
                    var className = 'geometry_' + data.toLowerCase();
                    $geometryInput.not('.' + className).hide();
                    if (!$('.' + className).is(":visible")) {
                        $('.' + className).show();
                    }
                })
                    .fail(function () {
                        console.log('fail');
                    })
            } else {
                $geometryInput.hide();
            }
        });
        $('#id_location_type').trigger('change');

    });
})(django.jQuery);