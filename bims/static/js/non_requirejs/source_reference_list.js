$('.copy-document-id').click(function (e) {
    let documentId = window.location.origin + '/documents/' + $(e.target).data('document-id');
    /* Copy the text inside the text field */
    navigator.clipboard.writeText(documentId);
    /* Alert the copied text */
    alert("Copied the text: " + documentId);
})

$('.custom-control-input').change(function (e) {
    let $parent = $(e.target).parent().parent();
    let filterName = $parent.data('filter');
    let checkedVals = $parent.find(':checkbox:checked').map(function () {
        return this.value;
    }).get();
    insertParam(filterName, checkedVals);
})

$('.input-group-append').click(function (e) {
    let value =  $('#search-input').val();
    insertParam('q', value);
})

$('.delete-reference').click(function (e) {
    e.preventDefault();
    const referenceId = $(e.target).data('reference-id');
    let r = confirm("Are you sure you want to remove this reference?");
    if (r === true) {
        $.ajax({
            url: "/delete-source-reference/",
            headers: {"X-CSRFToken": csrfToken},
            type: 'POST',
            data: {
                'reference_id': referenceId
            },
            success: function (res) {
                location.reload();
            }
        });
    }
})

$('.delete-records').click(function (e) {
    e.preventDefault();
    const referenceId = $(e.target).data('reference-id');
    const totalRecords = $(e.target).data('total-records');
    const totalPhysico = $(e.target).data('total-physico-chemical-data');
    let r = confirm(
        `Are you sure you want to remove ${totalRecords} records and ${totalPhysico} 
        Physico-chemical data associated with this source reference?`);

})


$('.apply-author-filter').click(function(e) {
    const $target = $(e.target).parent();
    const authorIds = $target.find('.author_result').map(function () {
        return $(this).data("author-id");
    }).get();
    insertParam('collectors', authorIds.join(','))
})
