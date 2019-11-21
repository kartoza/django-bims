let $bibliographyReference = $('#bibliography-reference');
let $studyReference = $('#study-reference');
let $databaseReference = $('#database-reference');
let $notesReference = $('#notes-reference');
let $referenceCategory = $('#reference-category');
let $notes = $('#notes-reference');

let showReferenceRow = ($row) => {
    $($row.closest('.references-row')).removeClass('hidden');
};

let categoryChanged = (value, _sourceReferenceId=null) => {
    /** called when category changed **/
    $('.references-row').addClass('hidden');
    switch (value) {
        case 'database':
            showReferenceRow($databaseReference);
            showReferenceRow($notesReference);
            if(_sourceReferenceId) {
                $databaseReference.val(_sourceReferenceId);
            }
            $notesReference.attr(
                "placeholder",
                "Provide any additional information about the database. E.g. The year created, the host, etc.");
            break;
        case 'bibliography':
            showReferenceRow($bibliographyReference);
            showReferenceRow($notesReference);
            if(_sourceReferenceId) {
                $("#doi-input").val(_sourceReferenceId);
                $('#fetch-doi-button').click();
            }
            $notesReference.attr(
                "placeholder",
                "If these data appear in other study references please specify those study references.");
            break;
        case 'document':
            showReferenceRow($studyReference);
            showReferenceRow($notesReference);
            if(_sourceReferenceId) {
                $studyReference.val(_sourceReferenceId);
            }
            $notesReference.attr(
                "placeholder",
                "If these data appear in other study references, please specify those study references.");
            break;
        case 'no-source':
            showReferenceRow($notesReference);
            $notesReference.attr(
                "placeholder",
                "Please specify the purpose of the data collected.");
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
        case 'no-source':
            if (!$notes.val()) {
                return 'Notes is empty.';
            }
            break;
    }
    return null
};

function renderDocumentInfo() {
    var $selectedOption = $('#study-reference option:selected');
    var year = $selectedOption.attr('year');
    var author = $selectedOption.attr('author');
    var title = $selectedOption.attr('title-doc');
    $('.table-info-document .body-table').html(
        '<td>'+ author +'</td>' +
        '<td>'+ year +'</td>' +
        '<td>'+ title +'</td>'
    )
}

$(document).ready(function () {
    renderDocumentInfo();

    $('#study-reference').change(function () {
        renderDocumentInfo()
    });
});

newDatabaseRecordSubmitCallback = (response) => {
    $databaseReference.append('<option value="' + response.id + '">' + response.name + '</option>');
    $databaseReference.val(response.id);
};

newDocumentSubmitCallback = (response) => {
    $studyReference.append('<option ' +
        'value="' + response.id + '" ' +
        'author="' + response.author + '" ' +
        'year="' + response.year + '" ' +
        'title-doc="' + response.title + '">' + response.title + '</option>');
    $studyReference.val(response.id);
    renderDocumentInfo();
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
            url: "/bibliography/api/fetch/by-doi/?q=" + encodeURIComponent($doiInput.val())
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
    if (referenceCategory) {
        $referenceCategory.val(referenceCategory.toLowerCase());
        $referenceCategory.find('option').each(function () {
            if ($(this).html().trim().toLowerCase() === referenceCategory.toLowerCase()) {
                $(this).attr('selected', 'selected');
                let _id = parseInt(sourceReferenceId);
                if (sourceReferenceDoi) {
                    _id = sourceReferenceDoi;
                }
                categoryChanged($(this).val(), _id);
                return true;
            }
        });
    }

    // submit
    let form = $('#source-reference-form');
    let $alertDiv = $('#form-alert');
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