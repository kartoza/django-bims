function formatTag (tag) {
    if (tag.loading) {
        return tag.text;
    }
    let $container = $(
        "<div class='select2-result-repository clearfix'>" +
        "<div class='select2-result-repository__meta'>" +
        "<div class='select2-result-repository__title'></div>" +
        "</div>" +
        "</div>"
    );
    if (tag.newTag) {
        $container.find(".select2-result-repository__title").text(`Add new tag : ${tag.text}`);
    } else {
        $container.find(".select2-result-repository__title").text(tag.name);
    }
    return $container;
}

function formatTagSelection (tag) {
    const tagName = tag.text || tag.name;
    return $(`<span class="tag_result" data-tag-id="${tagName}">${tagName}</span>`);
}

$(document).ready(function () {
    $('.tag-auto-complete').select2({
        ajax: {
            url: '/api/taxon-tag-autocomplete/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                };
            },
            processResults: function (data, params) {
                return {
                    results: data.map(_data => { return {
                        'id': _data.name,
                        'name': _data.name
                    }}),
                };
            },
            cache: true
        },
        placeholder: 'Search for a Tag',
        minimumInputLength: 3,
        templateResult: formatTag,
        templateSelection: formatTagSelection,
        tags: true,
        createTag: function (params) {
            if (!this.$element.data('add-new-tag')) {
                return null
            }
            let term = $.trim(params.term);

            if (term === '') {
                return null;
            }

            let exists = false;
            this.$element.find('option').each(function(){
                if ($.trim($(this).text()).toUpperCase() === term.toUpperCase()) {
                    exists = true;
                    return false;
                }
            });

            if (exists) {
                return null;
            }

            return {
                id: term,
                text: term,
                newTag: true
            };
        }

    });
    $('.save-tag').click(function () {
        let taxonomyId = $(this).data('taxonomy-id');
        let selectedTags = $('#taxa-tag-auto-complete').select2('data').map(tag => tag.text || tag.name);
        $.ajax({
            url: `/api/taxonomy/${taxonomyId}/add-tag/`,
            method: 'PUT',
            headers: {"X-CSRFToken": csrfToken},
            data: JSON.stringify({ tags: selectedTags }),
            contentType: 'application/json',
            success: function(response) {
                window.location.reload();
            },
            error: function(xhr, status, error) {
                console.error("Error adding tags:", error);
            }
        });
    });
});
