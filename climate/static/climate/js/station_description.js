$(function () {
    var $form = $('#station-description-form');
    if (!$form.length) {
        return;
    }
    var $text = $('#station-description');
    var $edit = $('#edit-station-description');
    var $error = $('#station-description-error');

    $edit.on('click', function (e) {
        e.preventDefault();
        $text.hide();
        $edit.hide();
        $form.show();
    });

    $('#cancel-station-description').on('click', function () {
        $error.text('');
        $form.hide();
        $text.show();
        $edit.show();
    });

    $('#save-station-description').on('click', function () {
        var $btn = $(this).prop('disabled', true);
        $.ajax({
            url: $form.data('url'),
            type: 'POST',
            data: {
                description: $('#station-description-input').val(),
                csrfmiddlewaretoken: $form.data('csrf')
            }
        }).done(function (data) {
            $text.text(data.description);
            $error.text('');
            $form.hide();
            $text.show();
            $edit.show();
        }).fail(function (xhr) {
            var msg = xhr.responseJSON && xhr.responseJSON.error;
            $error.text(msg || 'Unable to save the description.');
        }).always(function () {
            $btn.prop('disabled', false);
        });
    });
});
