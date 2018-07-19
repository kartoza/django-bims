$(function () {

    $('#process-shapefile').hide();
    $('#reupload-button').hide();

    $(".js-upload-photos").click(function () {
        $("#fileupload").click();
    });

    $("#fileupload").fileupload({
        acceptFileTypes: /(\.|\/)(shp|shx|dbf)$/i,
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
        $('#reupload-button').show();

        // Process shapefile
        $.ajax({
            url: processShapefileUrl,
            data: {
                token: csrfmiddlewaretoken
            },
            dataType: 'json',
            success: function (data) {
                $('#process-shapefile').html(data.message);
            }
        })

    })

    $('#reupload-button').click(function() {
        location.reload();
    });

});