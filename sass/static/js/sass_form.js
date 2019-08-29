const allowedInput = ['D', 'C', 'B', 'A', '1'];

$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    let submitButton = $('#submit');
    let dateValue = $('#date').val();
    let $frontendAlert = $('.frontend-alert');
    $frontendAlert.hide();
    if (!dateValue) {
        $('#cancel-submit').click();
        $frontendAlert.html('Missing date value').show();
        $('html, body').animate({
            scrollTop: 0}, 500);
        return false;
    }
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

function getGreatestRowValue(row) {
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
    return greatest;
}

function checkRatingScalePrevRow(currentRow, previousRow, deleted) {
    let prevScale = previousRow.find('.taxon-name').data('rating-scale');
    let ratingScale = currentRow.find('.taxon-name').data('rating-scale');

    if (prevScale) {
        if (ratingScale > prevScale) {
            let previousTotalRating = previousRow.find('.total-rating').val();
            if (previousTotalRating && !deleted) {
                previousRow.find('.total-rating').val('');
                previousRow.find('.total-rating').trigger('focusout');
            }
            if (!previousTotalRating && deleted) {
                // Check next row doesn't have total value
                let noTotalNextRow = true;
                let nextRow = currentRow.next();
                let nextRatingScale = nextRow.find('.taxon-name').data('rating-scale');
                while (nextRatingScale) {
                    noTotalNextRow = nextRow.find('.total-rating').val() === '';
                    nextRow = nextRow.next();
                    nextRatingScale = nextRow.find('.taxon-name').data('rating-scale');
                }
                if (noTotalNextRow) {
                    let greatest = getGreatestRowValue(previousRow);
                    if (greatest) {
                        previousRow.find('.total-rating').val(greatest);
                        previousRow.find('.total-rating').trigger('focusout');
                        return;
                    }
                }
            }
            checkRatingScalePrevRow(currentRow, previousRow.prev(), deleted);
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

function checkRatingScale(row, deleted) {
    let ratingScale = row.find('.taxon-name').data('rating-scale');
    if (!ratingScale) {
        return;
    }

    let nextRow = row.next();
    let previousRow = row.prev();

    checkRatingScaleNextRow(row, nextRow);
    checkRatingScalePrevRow(row, previousRow, deleted);
}

function userInputAutocomplete (inputIdName) {
    $('#'+inputIdName).autocomplete({
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
        change: function(event,ui){
            $(this).val((ui.item ? ui.item.label : ""));
        },
        select: function (e, u) {
            e.preventDefault();
            $('#accredited').prop("checked", false);
            $('#' + inputIdName).val(u.item.label);
            $('#' + inputIdName + '_id').val(u.item.value);
        }
    });
}

function closeSassForm(e) {
    window.history.back();
}

$(document).ready(function () {
    let totalTaxa = $.extend({}, biotope);
    let totalTaxaNumber = $.extend({}, biotope_number);
    let totalTaxaScore = $.extend({}, biotope_number);
    $('.sass-form-close').click(closeSassForm);

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

    $("#date").datepicker({
        changeMonth: true,
        changeYear: true
    });
    $('#time').timepicker({'timeFormat': 'H:i'});

    self.userInputAutocomplete('owner');
    self.userInputAutocomplete('collector');

    let $ratingInput = $('.rating-input');
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
            let greatest = getGreatestRowValue(row);
            let totalInput = row.find('.total-rating');
            totalInput.val(greatest);
            let deleted = !this.value && !greatest;
            if (deleted || totalInput.val()) {
                checkRatingScale(row, deleted);
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