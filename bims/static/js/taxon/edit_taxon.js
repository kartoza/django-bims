let treeDataCache = []
let initiated = false;

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

function formatSpeciesGroupSelection (data) {
    if (data.name) {
        return `${data.name}`
    }
    return data.text;
}

function formatSpeciesGroup (data) {
    if (data.loading) {
        return data.text;
    }
    let $container = $(
        "<div class='select2-result-repository clearfix'>" +
        "<div class='select2-result-repository__meta'>" +
        "<div class='select2-result-repository__title'></div>" +
        "</div>" +
        "</div>"
    );
    $container.find(".select2-result-repository__title").text(data.name);
    return $container;
}

function updateTaxonTree(_taxonId) {
    if ($('#taxon-tree').jstree(true)) {
        $('#taxon-tree').jstree('destroy');
    }

    if (treeDataCache.length > 0) {
        treeDataCache = treeDataCache.filter((cache) => cache['id'] == taxonId);
        treeDataCache[0]['parent'] = _taxonId
    }

    $('#taxon-tree').jstree({
        core: {
            data: function (node, cb) {
                $.getJSON(`/api/taxonomy-tree/${_taxonId}/`, function (data) {
                    treeDataCache.push(...data);
                    cb(treeDataCache);
                });
            },
            multiple: false,
            themes: { icons: false }
        },
        plugins: ['wholerow']
    }).on('loaded.jstree', function () {
        $('#taxon-tree').jstree('select_node', _taxonId.toString());
    });
}

$('#parent-taxon').change(function () {
    if (initiated) {
        updateTaxonTree(this.value);
    }
    initiated = true;
})

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

$('.species-group-auto-complete').select2({
  ajax: {
    url: '/species-group-autocomplete/',
    dataType: 'json',
    data: params => ({ term: params.term }),
    processResults: data => ({
      results: data.map(item => ({ id: String(item.id), text: item.name }))
    }),
    cache: true
  },
  placeholder: 'Search for a Species Group',
  minimumInputLength: 0,          // allow opening without typing
  allowClear: true,                // <-- enables the clear (x) button
  theme: 'classic',
  width: '100%',
  tags: true,
  createTag: (params) => {
    const term = (params.term || '').trim();
    if (!term) return null;
    return { id: 'NEW:' + term, text: `Create "${term}"`, isNew: true, rawText: term };
  },
  templateResult: (item) => item.isNew ? `➕ ${item.text}` : (item.text || item.name || ''),
  templateSelection: (item) => item.text || item.name || ''
});

$('.species-group-auto-complete').on('select2:clear', function () {
  $(this).val(null).trigger('change');
});

// $('.species-group-auto-complete').on('select2:select', function (e) {
//   const sel = e.params.data;
//   if (!sel || !String(sel.id).startsWith('NEW:')) return;
//
//   const term = sel.rawText || String(sel.id).replace(/^NEW:/, '').trim();
//   const $el = $(this);
//
//   $.ajax({
//     url: '/species-group-autocomplete/',
//     method: 'POST',
//     dataType: 'json',
//     data: { name: term },
//     headers: { 'X-CSRFToken': csrf_token }
//   }).done(function (res) {
//     const newOption = new Option(res.name, res.id, true, true);
//     $el.append(newOption).trigger('change');
//   }).fail(function (xhr) {
//     alert(xhr.responseJSON?.error || 'Failed to create Species Group.');
//     const values = ($el.val() || []).filter(v => v !== sel.id);
//     $el.val(values).trigger('change');
//   });
// });

document.addEventListener('DOMContentLoaded', function() {
    const taxonomicStatus = document.getElementById('taxonomic_status');
    const acceptedTaxonField = document.getElementById('accepted-taxon-field');

    updateTaxonTree(taxonId);

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

    if (speciesGroup) {
        let option = new Option(speciesGroup, speciesGroupId, true, true);
        let speciesGroupSelect = $('#species-group');
        speciesGroupSelect.append(option).trigger('change');
        speciesGroupSelect.trigger({
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

