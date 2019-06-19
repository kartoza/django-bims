$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    let submitButton = $('#submit');
    submitButton.addClass('disabled');
    let submitMessage = submitButton.data('message');
    if (submitMessage) {
        submitButton.html(submitMessage);
    } else {
        submitButton.html('Updating...');
    }
    $('#cancel-submit').hide();
    $('#sass-form').submit();
});

let biotope = {
    'stones': {},
    'vegetation': {},
    'gsm': {},
    'total': {}
};

let biotope_number = {
    'stones': 0,
    'vegetation': 0,
    'gsm': 0,
    'total': 0
};

function calculateTaxa(bio, bioObject, totalTaxaNumber, totalTaxaScore) {
    let notEmptyInputs = $('#taxon-list').find("[data-biotope='" + bio + "']").filter(function () {
        return this.value !== '';
    });
    $.each(notEmptyInputs, function (index, input) {
        let id = $(input).data('id');
        if (!bioObject[bio].hasOwnProperty(id)) {
            // get score
            let scoreDiv = $(input).parent().parent().find('.taxon-name');
            bioObject[bio][id] =  scoreDiv.data('score');
            totalTaxaScore[bio] += parseInt(scoreDiv.data('score'));
        }
    });
    totalTaxaNumber[bio] = notEmptyInputs.length;
}

function checkRatingScalePrevRow(currentRow, previousRow) {
    let prevScale = previousRow.find('.taxon-name').data('rating-scale');
    let ratingScale = currentRow.find('.taxon-name').data('rating-scale');

    if (prevScale) {
        if (ratingScale > prevScale) {
            let previousTotalRating = previousRow.find('.total-rating').val();
            if (previousTotalRating) {
                previousRow.find('.total-rating').val('');
                previousRow.find('.total-rating').trigger('focusout');
            }
            checkRatingScalePrevRow(currentRow, previousRow.prev());
        }
    }
}

function checkRatingScaleNextRow(currentRow, nextRow) {
    let nextScale = nextRow.find('.taxon-name').data('rating-scale');
    let ratingScale = currentRow.find('.taxon-name').data('rating-scale');

    if (nextScale) {
        if (nextScale > ratingScale) {
            let nextRowHasValue = false;
            $(nextRow.find('.rating-input')).each(function () {
                if ($(this).val()) {
                    nextRowHasValue = true;
                    return true;
                }
            });
            if (nextRowHasValue) {
                currentRow.find('.total-rating').val('');
            } else {
                checkRatingScaleNextRow(currentRow, nextRow.next());
            }
        }
    }
}

function checkRatingScale(row) {
    let ratingScale = row.find('.taxon-name').data('rating-scale');
    if (!ratingScale) {
        return;
    }

    let nextRow = row.next();
    let previousRow = row.prev();

    checkRatingScaleNextRow(row, nextRow);
    checkRatingScalePrevRow(row, previousRow);
}

$(document).ready(function () {
    let totalTaxa = $.extend({}, biotope);
    let totalTaxaNumber = $.extend({}, biotope_number);
    let totalTaxaScore = $.extend({}, biotope_number);

    $.each(biotope_number, function (key, value) {
        calculateTaxa(key, totalTaxa, totalTaxaNumber, totalTaxaScore);
        $('#number-taxa-' + key).html(totalTaxaNumber[key]);
        $('#sass-score-' + key).html(totalTaxaScore[key]);
        let aspt = parseFloat(totalTaxaScore[key]) / parseFloat(totalTaxaNumber[key]);
        if(aspt) {
            $('#aspt-' + key).html(aspt.toFixed(1));
        }
    });

    let allInputText = $("input[type='text']");
    allInputText.on("click", function () {
        $(this).select();
    });
    $('#sass-form').submit(function () {
        let emptyInputFields = allInputText.filter(function () {
            return this.value === '';
        });
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
            if (totalInput.val()) {
                checkRatingScale(row);
            }

        }
    });

    $ratingInput.on('focusout', function (e) {
        let biotope = $(this).data('biotope');
        let id = $(this).data('id');
        let scoreDiv = $(this).parent().parent().find('.taxon-name');

        if (!this.value) {
            if (totalTaxa[biotope].hasOwnProperty(id)) {
                delete totalTaxa[biotope][id];
                totalTaxaNumber[biotope] -= 1;
                totalTaxaScore[biotope] -= parseInt(scoreDiv.data('score'));
            }
        } else {
            if (!totalTaxa[biotope].hasOwnProperty(id)) {
                totalTaxa[biotope][id] = scoreDiv.data('score');
                totalTaxaNumber[biotope] += 1;
                totalTaxaScore[biotope] += parseInt(scoreDiv.data('score'));
            }
        }

        $('#number-taxa-' + biotope).html(totalTaxaNumber[biotope]);
        $('#sass-score-' + biotope).html(totalTaxaScore[biotope]);
        let aspt = parseFloat(totalTaxaScore[biotope]) / parseFloat(totalTaxaNumber[biotope]);
        if (!aspt) {
            aspt = 0;
        }
        $('#aspt-' + biotope).html(aspt.toFixed(1));

        // Need to update total column
        if (biotope !== 'total') {
            let total = $('#taxon-list').find("[data-id='" + id + "'].total-rating");
            total.trigger('focusout');
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