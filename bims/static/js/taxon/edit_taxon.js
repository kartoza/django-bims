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

$('#rank').change(function () {
})

$('.taxa-auto-complete').select2({
    ajax: {
        url: '/species-autocomplete/',
        dataType: 'json',
        data: function (params) {
            return {
                term: params.term,
                rank: $(this).data('rank')
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


document.addEventListener('DOMContentLoaded', function() {
    const taxonomicStatus = document.getElementById('taxonomic_status');
    const acceptedTaxonField = document.getElementById('accepted-taxon-field');

    function toggleAcceptedTaxonField() {
        if (taxonomicStatus.value === 'SYNONYM') {
            acceptedTaxonField.style.display = 'flex';
        } else {
            acceptedTaxonField.style.display = 'none';
        }
    }

    toggleAcceptedTaxonField();

    taxonomicStatus.addEventListener('change', toggleAcceptedTaxonField);

    if (parent) {
        let option = new Option(parent, parentId, true, true);
        let parentTaxon = $('#parent-taxon');
        parentTaxon.append(option).trigger('change');
        parentTaxon.trigger({
            type: 'select2:select',
            params: {
                data: {}
            }
        });
    }

    if (acceptedTaxonomy) {
        let option = new Option(acceptedTaxonomy, acceptedTaxonomyId, true, true);
        let acceptedTaxon = $('#accepted-taxon');
        acceptedTaxon.append(option).trigger('change');
        acceptedTaxon.trigger({
            type: 'select2:select',
            params: {
                data: {}
            }
        });
    }

    if (tagList.length > 0) {
        const tagAutoComplete = $('#taxa-tag-auto-complete');
        tagAutoComplete.empty().val(null).trigger('change');
        const tagIds = [];
        tagList.forEach(tag => {
            let newOption = new Option(tag, tag, false, false);
            tagAutoComplete.append(newOption);
            tagIds.push(tag);
        });
        tagAutoComplete.val(tagIds).trigger('change');
    }

    if (biographicDistributions.length > 0) {
        const bDAutoComplete = $('#biographic-tag-auto-complete');
        bDAutoComplete.empty().val(null).trigger('change');
        const tagIds = [];
        biographicDistributions.forEach(tag => {
            let newOption = new Option(tag, tag, false, false);
            bDAutoComplete.append(newOption);
            tagIds.push(tag);
        });
        bDAutoComplete.val(tagIds).trigger('change');
    }

});

