$(function () {

    $('#process-shapefile').hide();

    $(".js-upload-photos").click(function () {
        $("#fileupload").click();
    });

    $("#fileupload").fileupload({
        dataType: 'json',
        done: function (e, data) {
            if (data.result.is_valid) {
                $("#gallery tbody").prepend(
                    "<tr><td><a href='" + data.result.url + "'>" + data.result.name + "</a></td></tr>"
                )
            }
        }
    });

    $('#fileupload').bind('fileuploadstop', function (e) {
        $('.js-upload-photos').hide();

        $('#process-shapefile').show();

        // Process shapefile
        $.ajax({
            url: '/process_shapefiles/',
            data: {
                token: csrfmiddlewaretoken
            },
            dataType: 'json',
            success: function (data) {
                $('#process-shapefile').html(data.message);
            }
        })

    })

});