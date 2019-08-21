let $bibliographyReference = $('#bibliography-reference');
let $studyReference = $('#study-reference');
let $databaseReference = $('#database-reference');
let $notesReference = $('#notes-reference');
let $referenceCategory = $('#reference-category');

let showReferenceRow = ($row) => {
    $($row.closest('.references-row')).removeClass('hidden');
};

let categoryChanged = (value) => {
    /** called when category changed **/
    $('.references-row').addClass('hidden');
    switch (value) {
        case 'database':
            showReferenceRow($databaseReference);
            showReferenceRow($notesReference);
            break;
        case 'bibliography':
            showReferenceRow($bibliographyReference);
            showReferenceRow($notesReference);
            break;
        case 'document':
            showReferenceRow($studyReference);
            showReferenceRow($notesReference);
            break;
        case 'no-source':
            showReferenceRow($notesReference);
            break;
    }
};

let categoryValidation = (value) => {
    switch (value) {
        case 'database':
            if (!$databaseReference.val()) {
                return 'Database is not selected yet.';
            }
            break;
        case 'bibliography':
            if (!$bibliographyReference.val()) {
                return 'DOI is not correct.';
            }
            break;
        case 'document':
            if (!$studyReference.val()) {
                return 'Study reference is not selected yet.';
            }
            break;
    }
    return null
};

$(function () {
    // DOI handler
    var $bibliographyTitle = $('#bibliography-title');
    var $doiInput = $("#doi-input");
    $('#fetch-doi-button').click(function () {
        $bibliographyReference.val('');
        $bibliographyTitle.html('');
        $bibliographyTitle.removeClass('error');
        if (!$doiInput.val()) {
            return;
        }
        $bibliographyTitle.html('<i>loading</i>');
        $.ajax({
            url: "/bibliography/api/fetch/by-doi/?q=" + $doiInput.val()
        })
            .done(function (data) {
                $bibliographyReference.val(data['id']);
                $bibliographyTitle.html('' + data['full_title'])
            })
            .fail(function (error) {
                $bibliographyTitle.addClass('error');
                $bibliographyTitle.html(error['responseText'])
            })
        ;
    });
    $referenceCategory.change(function () {
        categoryChanged($referenceCategory.val());
    });
    $('.references-row').addClass('hidden');

    // submit
    let form = $('#source-reference-form');
    let $alertDiv = $('.alert-danger');
    $('#submit').click((event) => {
        $alertDiv.hide();
        let alertMessage = null;
        if (!$referenceCategory.val()) {
            alertMessage = 'Category is not selected yet';
        } else {
            alertMessage = categoryValidation($referenceCategory.val());
        }
        if (alertMessage) {
            $alertDiv.html(alertMessage);
            $alertDiv.show();
            event.preventDefault();
            event.stopPropagation();
            $('#confirm-submit').modal('hide');
            setTimeout(function () {
                window.scrollTo(0, 0);
            }, 500);
            return;
        }
        form.submit();
        return;
    });
});