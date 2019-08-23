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
    $notesReference.val('');
    switch (value) {
        case 'database':
            showReferenceRow($databaseReference);
            showReferenceRow($notesReference);
            $notesReference.attr(
                "placeholder",
                "Provide any additional information about the database. E.g. The year created, the host, etc.");
            break;
        case 'bibliography':
            showReferenceRow($bibliographyReference);
            showReferenceRow($notesReference);
            $notesReference.attr(
                "placeholder",
                "Provide any additional information about study reference. " +
                "E.g. Data extracted from Shelton, J.M., 2013 PhD thesis - Shelton, J.M., 2013. " +
                "Impact of non-native rainbow trout on stream food webs in the Cape Floristic Region, South Africa intergrating evidence from surveys and experiments." +
                "University of Cape Town.");
            break;
        case 'document':
            showReferenceRow($studyReference);
            showReferenceRow($notesReference);
            $notesReference.attr(
                "placeholder",
                "Provide any additional information about study reference. " +
                "E.g. Data from the report was used in Dallas, H.F. & Rivers-Moore, N.A., 2012 paper (10.1007/s10750-011-0856-4).");
            break;
        case 'no-source':
            showReferenceRow($notesReference);
            $notesReference.attr(
                "placeholder",
                "Provide any additional information about the unpublished data. E.g. I went on a hiking trip to the Cederberg and saw Galaxias Zebratus in the Olifants River.");
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

newDocumentSubmitCallback = (response) => {
    $studyReference.append('<option value="' + response.id + '">' + response.title + '</option>');
    $studyReference.val(response.id);
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