function formatTaxa (taxa) {
    if (taxa.loading) {
        return taxa.text;
    }
    let $container = $(
        "<div class='select2-result-repository clearfix'>" +
        "<div class='select2-result-repository__meta'>" +
        "<div class='select2-result-repository__title'></div>" +
        "<div class='select2-result-repository__description'></div>" +
        "</div>" +
        "</div>"
    );
    $container.find(".select2-result-repository__title").text(taxa.species);
    $container.find(".select2-result-repository__description").text(taxa.rank);
    return $container;
}

function formatTaxaSelection (taxa) {
    if (taxa.species) {
        return `${taxa.species} (${taxa.rank})`
    }
    return taxa.text;
}

const taxaAutoComplete = $('#taxa-auto-complete').select2({
    ajax: {
        url: '/species-autocomplete/',
        dataType: 'json',
        data: function (params) {
            return {
                term: params.term,
                taxonGroupId: taxonGroupId
            }
        },
        processResults: function (data) {
            return {
                results: data
            }
        },
        cache: true
    },
    placeholder: 'Search for a Taxonomy',
    minimumInputLength: 3,
    templateResult: formatTaxa,
    templateSelection: formatTaxaSelection,
    theme: "classic"
});

if (parent) {
    let option = new Option(parent, parentId, true, true);
    taxaAutoComplete.append(option).trigger('change');
    taxaAutoComplete.trigger({
        type: 'select2:select',
        params: {
            data: {}
        }
    });
}