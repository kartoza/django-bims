$('#owner').autocomplete({
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
    minLength: 3,
    open: function (event, ui) {
        setTimeout(function () {
            $('.ui-autocomplete').css('z-index', 99);
        }, 0);
    },
    change: function (event, ui) {
        let $ownerIdInput = $('#owner_id');
        if (ui.item) {
            $ownerIdInput.val(ui.item.value);
        } else {
            $('#owner').val(' ');
            $ownerIdInput.val(' ');
        }
    },
    select: function (e, u) {
        e.preventDefault();
        $('#owner').val(u.item.label);
        $('#owner_id').val(u.item.value);
    }
});