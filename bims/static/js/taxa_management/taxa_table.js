export const taxaTable = (() => {
    const fullUrl = new URL(window.location.href);
    const urlParams = fullUrl.searchParams;
    const filterSelected = {};
    const $clearSearchBtn = $('#clear-search-button');
    const $searchBtn = $('#search-button');
    let $validateTaxonBtn = $('.validate-taxon');
    let $rejectTaxonBtn = $('.reject-taxon');
    let $rejectTaxonConfirmBtn = $('#rejectBtn');

    let taxaListCurrentUrl = '';
    let totalAllFilters = 0;
    let url = '';
    let selectedTaxonGroup = '';


    function init(getTaxaList, _selectedTaxonGroup) {
        selectedTaxonGroup = _selectedTaxonGroup;

        $('[data-toggle="tooltip"]').tooltip();
        $('[data-toggle="popover"]').popover();
        initSelect2Components();
        handleUrlParameters();
        if (url) {
            getTaxaList(url);
        }
        $('.select-multiple').select2();
        $('#apply-filters').on('click', handleFilters)
        $clearSearchBtn.on('click', handleClearFilters)
        $searchBtn.on('click', handleSearch)
        $validateTaxonBtn.on('click', handleValidateTaxon)
        $rejectTaxonBtn.on('click', handleRejectTaxon)
        $rejectTaxonConfirmBtn.on('click', handleConfirmRejectTaxon)

        $('.remove-taxon-from-group').on('click', handleRemoveTaxonFromGroup)

        $('.sort-button').on('click', handleSortButtonClicked)

        $('#collapseFilter').on('shown.bs.collapse', function() {
            $('#add-filters').find('i').removeClass('fa-chevron-down').addClass('fa-chevron-up');
        }).on('hidden.bs.collapse', function() {
            $('#add-filters').find('i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
        })
    }

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

    function initSelect2Components() {
        $('#edit-module-taxa-autocomplete').select2({
            dropdownParent: $("#editModuleModal"),
            ajax: {
                url: '/species-autocomplete/',
                dataType: 'json',
                data: function (params) {
                    return {
                        term: params.term,
                        taxonGroupId: $('#editModuleModal').data('module')
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

        $('#taxa-auto-complete').select2({
            ajax: {
                url: '/species-autocomplete/',
                dataType: 'json',
                data: function (params) {
                    return {
                        term: params.term,
                        taxonGroupId: urlParams.get('selected')
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
    }

    function handleUrlParameters() {
        let taxonName = '';
        if (selectedTaxonGroup) {
            $('#sortable').find(`[data-id="${selectedTaxonGroup}"]`).addClass('selected');
            url = `/api/taxa-list/?taxonGroup=${selectedTaxonGroup}`
        }
        if (urlParams.get('validated')) {
            const validated = urlParams.get('validated');
            if (url) {
                url += `&validated=${validated}`;
                $('#validated').val(validated);
            }
        }
        if (urlParams.get('taxon')) {
            taxonName = urlParams.get('taxon');
            if (url) {
                url += `&taxon=${taxonName}`
                $('#taxon-name-input').val(taxonName)
                $clearSearchBtn.show();
            }
        }
        if (urlParams.get('o')) {
            const order = urlParams.get('o');
            if (url) {
                $(`.sort-button[data-order="${order}"]`).addClass('sort-button-selected');
                url += `&o=${order}`
            }
        }
        if (urlParams.get('page')) {
            url += `&page=${urlParams.get('page')}`;
        }
        if (urlParams.get('ranks')) {
            const ranksArray = urlParams.get('ranks').split(',');
            $('#rank-filters').val(ranksArray);
            filterSelected['ranks'] = ranksArray;
            totalAllFilters += ranksArray.length;
            url += `&ranks=${urlParams.get('ranks')}`;
        }
        if (urlParams.get('origins')) {
            const originsArray = urlParams.get('origins').split(',');
            $('#origin-filters').val(originsArray);
            filterSelected['origins'] = originsArray;
            totalAllFilters += originsArray.length;
            url += `&origins=${urlParams.get('origins')}`;
        }
        if (urlParams.get('tags')) {
            const tagsArray = urlParams.get('tags').split(',');
            const tagAutoComplete = $('#tag-filters');
            tagAutoComplete.empty();
            tagAutoComplete.val(null).trigger('change');
            if (tagsArray.length > 0) {
                const tagIds = []
                tagsArray.forEach(tag => {
                    let newOption = new Option(
                        tag, tag, false, false);
                    tagAutoComplete.append(newOption);
                    tagIds.push(tag);
                });
                tagAutoComplete.val(tagIds);
                tagAutoComplete.trigger('change');
            }
            filterSelected['tags'] = tagsArray;
            totalAllFilters += tagsArray.length;
            url += `&tags=${urlParams.get('tags')}`;
        }
        if (urlParams.get('endemism')) {
            const endemismArray = urlParams.get('endemism').split(',');
            $('#endemism-filters').val(endemismArray);
            filterSelected['endemism'] = endemismArray;
            totalAllFilters += endemismArray.length;
            url += `&endemism=${urlParams.get('endemism')}`;
        }
        if (urlParams.get('is_gbif')) {
            url += `&is_gbif=${urlParams.get('is_gbif')}`;
        }
        if (urlParams.get('is_iucn')) {
            url += `&is_iucn=${urlParams.get('is_iucn')}`;
        }
        if (urlParams.get('cons_status')) {
            const consStatusArray = urlParams.get('cons_status').split(',');
            $('#cons-status-filters').val(consStatusArray);
            filterSelected['cons_status'] = consStatusArray;
            totalAllFilters += consStatusArray.length;
            url += `&cons_status=${urlParams.get('cons_status')}`;
        }
        if (urlParams.get('validated')) {
            const validatedValue = urlParams.get('validated');
            url += `&validated=${urlParams.get('validated')}`;
            if (validatedValue === 'False') {
                filterSelected['validated'] = urlParams.get('validated');
                totalAllFilters += 1;
            }
        }
        if (urlParams.get('parent')) {
            const parentArray = urlParams.get('parent').split(',');
            const taxaAutoComplete = $('#taxa-auto-complete');
            filterSelected['parent'] = parentArray;
            $.ajax({
                type: 'GET',
                url: `/api/taxa-list/?taxonGroup=${selectedTaxonGroup}&id=${urlParams.get('parent')}`,
            }).then(function (data) {
                // create the option and append to Select2
                if (data.length === 0) return false;
                let result = data[0];
                let option = new Option(
                    `${result['canonical_name']} (${result['rank']})`, result.id, true, true);
                taxaAutoComplete.append(option).trigger('change');
                taxaAutoComplete.trigger({
                    type: 'select2:select',
                    params: {
                        data: data
                    }
                });
            });
            totalAllFilters += parentArray.length;
            url += `&parent=${urlParams.get('parent')}`;
        }
        if (Object.keys(filterSelected).length > 0) {
            $clearSearchBtn.show();
            $('#total-selected-filter').html(totalAllFilters);
        }
    }

    function handleFilters(event) {
        const ranks = $('#rank-filters').select2('data').map(function(data) {
            return data['text'];
        })
        let urlParams = insertParam('ranks', ranks.join(), true, false);
        const origins = $('#origin-filters').select2('data').map(function(data) {
            return data['id'];
        })
        urlParams = insertParam('origins', origins.join(), true, false, urlParams);
        const endemism = $('#endemism-filters').select2('data').map(function(data) {
            return data['text'];
        })
        urlParams = insertParam('endemism', endemism.join(), true, false, urlParams);
        const consStatus = $('#cons-status-filters').select2('data').map(function(data) {
            return data['id'];
        })
        urlParams = insertParam('cons_status', consStatus.join(), true, false, urlParams);

        const parent = $('#taxa-auto-complete').select2('data').map(function(data) {
            return data['id'];
        })
        urlParams = insertParam('parent', parent.join(), true, false, urlParams);

        const validated = $('#validated').find(":selected").val();
        urlParams = insertParam('validated', validated, true, false, urlParams);

        const tags = $('#tag-filters').val();
        urlParams = insertParam('tags', tags, true, false, urlParams);

        document.location.search = urlParams;
    }

    function handleClearFilters(event) {
        let urlParams = document.location.search.substr(1);
        if (Object.keys(filterSelected).length > 0) {
            $.each(filterSelected, function (key, value) {
                urlParams = insertParam(key, '', true, false, urlParams);
            })
        }
        urlParams = insertParam('taxon', '', true, false, urlParams);
        document.location.search = urlParams;
    }

    function handleSearch(event) {
        if (!url) {
            return true;
        }
        let taxonNameInput = $('#taxon-name-input');
        let taxonName = taxonNameInput.val();
        insertParam('taxon', taxonName);
    }

    function handleValidateTaxon(e) {
        e.preventDefault();
        let $target = $(e.target);
        let currentTry = 0;
        while (!$target.hasClass('taxa-row') && currentTry < 10) {
            currentTry += 1;
            $target = $target.parent();
        }
        let id = $target.data('id');
        let r = confirm("Are you sure you want to validate this taxon?");
        if (r === true) {
            $.ajax({
                url: approveUrl + id + '/' + selectedTaxonGroup + '/',
                headers: {"X-CSRFToken": csrfToken},
                type: 'PUT',
                data: {
                    'action': 'approve'
                },
                success: function () {
                    alert('Taxon is successfully validated.');
                    location.reload()
                },
                error: function (e) {
                    alert('Something is wrong, please try again.');
                    console.log(e)
                    // location.reload()
                }
            })
        }
    }

    function handleRejectTaxon(e) {
        e.preventDefault();
        const modal = $('#confirmRejectModal');
        let $target = $(e.target);
        let currentTry = 0;
        while (!$target.hasClass('taxa-row') && currentTry < 10) {
            currentTry += 1;
            $target = $target.parent();
        }
        let id = $target.data('id');
        modal.find('.rejection-message').val('');
        modal.modal('show');
        modal.data('id', id);
    }

    function handleConfirmRejectTaxon(e) {
        const modal = $('#confirmRejectModal');
        const id = modal.data('id');
        const rejectionMessage = modal.find('.rejection-message').val();
        $.ajax({
            url: rejectUrl + id + '/' + selectedTaxonGroup + '/',
            headers: {"X-CSRFToken": csrfToken},
            type: 'PUT',
            data: {
                'action': 'reject',
                'comments': rejectionMessage
            },
            success: function () {
                alert('Taxon is successfully rejected.');
                location.reload()
            },
            error: function () {
                alert('Something is wrong, please try again.');
                location.reload()
            }
        })
    }

    function removeTaxonFromTaxonGroup(taxaId) {
        let $taxonGroupCard = $(`#taxon_group_${selectedTaxonGroup}`);
        $.ajax({
            url: '/api/remove-taxa-from-taxon-group/',
            headers: {"X-CSRFToken": csrfToken},
            type: 'POST',
            data: {
                'taxaIds': JSON.stringify([taxaId]),
                'taxonGroupId': selectedTaxonGroup
            },
            success: function (response) {
                $taxonGroupCard.html(response['taxonomy_count']);
                location.reload();
            }
        });
    }

    function handleRemoveTaxonFromGroup(e) {
        let r = confirm("Are you sure you want to remove this taxon from the group?");
        if (r === true) {
            let $target = $(e.target);
            let maxTry = 10;
            let currentTry = 0;
            while (!$target.hasClass('taxa-row') && currentTry < maxTry) {
                currentTry += 1;
                $target = $target.parent();
            }
            let id = $target.data('id');
            removeTaxonFromTaxonGroup(id);
        }
    }

    function handleSortButtonClicked(e) {
        let $target = $(event.target);
        let order = $target.data('order');
        if (order) {
            insertParam('o', order);
        }
    }

    return {
        init,
    };
})();
