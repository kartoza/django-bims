$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    $('#sass-form').submit();
});

$(document).ready(function () {
    if (isUpdate) {
        $('#submitBtn').val('Update');
    }
    $("#date").datepicker({
        changeMonth: true,
        changeYear: true
    });
    $('#time').timepicker({ 'timeFormat': 'H:i' });
});