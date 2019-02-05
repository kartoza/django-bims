$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    $('#sass-form').submit();
});

$(document).ready(function () {
    $("input[type='text']").on("click", function () {
        $(this).select();
    });
    if (isUpdate) {
        $('#submitBtn').val('Update');
    }
    $("#date").datepicker({
        changeMonth: true,
        changeYear: true
    });
    $('#time').timepicker({'timeFormat': 'H:i'});
    $('#assessor').autocomplete({
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
            $('#assessor').val(u.item.label);
            $('#assessor_id').val(u.item.value);
        }
    })
});