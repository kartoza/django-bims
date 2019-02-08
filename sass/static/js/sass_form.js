$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    $('#sass-form').submit();
});

$(document).ready(function () {

    let allInputText = $("input[type='text']");
    allInputText.on("click", function () {
        $(this).select();
    });
    $('#sass-form').submit(function () {
        let emptyInputFields = allInputText.filter(function() { return this.value === ''; });
        emptyInputFields.attr("disabled", true);
        return true;
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
    });

    let $ratingInput = $('.rating-input');
    let allowedInput = ['D', 'C', 'B', 'A', '1'];
    $ratingInput.on('keypress', function (e) {
        let char = e.key;
        char = char.toUpperCase();
        if (allowedInput.indexOf(char) === -1) {
            return false
        }
    });
    $ratingInput.on('keyup', function (e) {
        this.value = this.value.toUpperCase();
        if ($(this).hasClass('total-rating')) {
            return true;
        } else {
            let row = $(this).parent().parent();
            let greatest = '';
            $.each(row.find('td'), function (index, td) {
                let input = $($(td).find('input')[0]);
                if (input.hasClass('rating-input') && !input.hasClass('total-rating')) {
                    let inputValue = input.val();
                    if (!inputValue) {
                        return true;
                    }
                    if (!greatest) {
                        greatest = inputValue;
                    } else {
                        let greatestIndex = allowedInput.indexOf(greatest);
                        let inputIndex = allowedInput.indexOf(inputValue);
                        if (inputIndex < greatestIndex) {
                            greatest = inputValue;
                        }
                    }
                }
            });
            let totalInput = row.find('.total-rating');
            totalInput.val(greatest);
        }
    });

    $('#data-source').autocomplete({
        source: function (request, response) {
            $.ajax({
                url: '/data-source-autocomplete/?term=' + encodeURIComponent(request.term),
                type: 'get',
                dataType: 'json',
                success: function (data) {
                    response($.map(data, function (item) {
                        return {
                            label: item.name,
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
            $('#data-source').val(u.item.label);
            $('#data-source-id').val(u.item.value);
        }
    });

});