function formatAuthor(author) {
    if (author.loading) {
        return author.text;
    }
    let $container = $(
        "<div class='select2-result-repository clearfix'>" +
        "<div class='select2-result-repository__meta'>" +
        "<div class='select2-result-repository__title'></div>" +
        "</div>" +
        "</div>"
    );
    $container.find(".select2-result-repository__title").text(author.first_name + ' ' + author.last_name);
    return $container;
}

function formatAuthorSelection(author) {
    const authorName = author.text || author.first_name + " " + author.last_name
    return $(`<span class="author_result" data-author-id="${author.id}">${authorName}</span>`);
}

let authorSelect = $('.owner-auto-complete').select2({
    ajax: {
        url: "/user-autocomplete/",
        dataType: "json",
        delay: 250,
        data: function (params) {
            return {
                term: params.term
            }
        },
        processResults: function (data, params) {
            // parse the results into the format expected by Select2
            // since we are using custom formatting functions we do not need to
            // alter the remote JSON data, except to indicate that infinite
            // scrolling can be used
            params.page = params.page || 1;
            return {
                results: data,
                pagination: {
                    more: (params.page * 30) < data.total_count
                }
            };
        },
        cache: true
    },
    placeholder: 'Search for a author',
    minimumInputLength: 3,
    templateResult: formatAuthor,
    templateSelection: formatAuthorSelection
})
