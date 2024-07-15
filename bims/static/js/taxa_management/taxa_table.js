export const taxaTable = (() => {
    const fullUrl = new URL(window.location.href);
    const urlParams = fullUrl.searchParams;
    const filterSelected = {};
    const $clearSearchBtn = $('#clear-search-button');
    const $searchBtn = $('#search-button');
    let $rejectTaxonConfirmBtn = $('#rejectBtn');

    let taxaListCurrentUrl = '';
    let totalAllFilters = 0;
    let url = '';
    let selectedTaxonGroup = '';

    function convertAuthorStringToArray(authorString) {
        authorString = decodeURIComponent(authorString)
        // Split the string by comma between quotes
        const regex = /"([^"]+)"/g;
        const authorsArray = [];
        let match;

        while ((match = regex.exec(authorString)) !== null) {
            // Decode the author string
            authorsArray.push(decodeURIComponent(match[1]));
        }

        return authorsArray;
    }


    function init(getTaxaList, _selectedTaxonGroup) {
        selectedTaxonGroup = _selectedTaxonGroup;

        initSelect2Components();
        handleUrlParameters();
        if (url) {
            getTaxaList(url);
        }
        $('.select-multiple').select2();
        $('#apply-filters').on('click', handleFilters)
        $clearSearchBtn.on('click', handleClearFilters)
        $searchBtn.on('click', handleSearch)
        $rejectTaxonConfirmBtn.on('click', handleConfirmRejectTaxon)

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

        $('.taxon-auto-complete').select2({
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
    }

    function handleUrlParameters() {
        let taxonName = '';
        if (selectedTaxonGroup) {
            $('#sortable').find(`[data-id="${selectedTaxonGroup}"]`).addClass('selected');
            url = `/api/taxa-list/?taxonGroup=${selectedTaxonGroup}`
        }

        let validated = 'True'
        if (urlParams.get('validated')) {
            validated = urlParams.get('validated');
        }
        if (url) {
            url += `&validated=${validated}`;
        }
        $(`input[name="validated"][value="${validated}"]`).prop('checked', true);

        let tagFilterType = 'OR';
        if (urlParams.get('tagFT')) {
            tagFilterType = urlParams.get('tagFT');
        }
        if (url) {
            url += `&tagFT=${tagFilterType}`;
        }
        $(`input[name="tag-filter-type"][value="${tagFilterType}"]`).prop('checked', true);

        let bDFilterType = 'OR';
        if (urlParams.get('bDFT')) {
            bDFilterType = urlParams.get('bDFT');
        }
        if (url) {
            url += `&bDFT=${bDFilterType}`;
        }
        $(`input[name="biographic-distributions-filter-type"][value="${bDFilterType}"]`).prop('checked', true);

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
        if (urlParams.get('bD')) {
            const bDArray = urlParams.get('bD').split(',');
            const bDAutoComplete = $('#biographic-distributions-filters');
            bDAutoComplete.empty();
            bDAutoComplete.val(null).trigger('change');
            if (bDArray.length > 0) {
                const tagIds = []
                bDArray.forEach(tag => {
                    let newOption = new Option(
                        tag, tag, false, false);
                    bDAutoComplete.append(newOption);
                    tagIds.push(tag);
                });
                bDAutoComplete.val(tagIds);
                bDAutoComplete.trigger('change');
            }
            filterSelected['bD'] = bDArray;
            totalAllFilters += bDArray.length;
            url += `&bD=${urlParams.get('bD')}`;
        }
        if (urlParams.get('author')) {
            const authorArray = convertAuthorStringToArray(urlParams.get('author'));
            const authorAutoComplete = $('#author-filters');
            authorAutoComplete.empty();
            authorAutoComplete.val(null).trigger('change');
            if (authorArray.length > 0) {
                const tagIds = []
                authorArray.forEach(tag => {
                    let newOption = new Option(
                        tag, tag, false, false);
                    authorAutoComplete.append(newOption);
                    tagIds.push(tag);
                });
                authorAutoComplete.val(tagIds);
                authorAutoComplete.trigger('change');
            }
            filterSelected['author'] = authorArray;
            totalAllFilters += authorArray.length;
            url += `&author=${urlParams.get('author')}`;
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

        for (const taxaRank of ['family', 'genus', 'species']) {
            if (urlParams.get(taxaRank)) {
                const filterArray = urlParams.get(taxaRank).split(',');
                const autoComplete = $(`#${taxaRank}-auto-complete`);
                filterSelected[taxaRank] = filterArray;

                for (const taxaFilterValue of filterArray) {
                    let option = new Option(
                        `${taxaFilterValue} (${taxaRank.toUpperCase()})`, taxaFilterValue, true, true);
                    autoComplete.append(option).trigger('change');
                    autoComplete.trigger({
                        type: 'select2:select',
                    });

                }
                totalAllFilters += filterArray.length;
                url += `&${taxaRank}=${urlParams.get(taxaRank)}`;
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
        try {
            const origins = $('#origin-filters').select2('data').map(function(data) {
                return data['id'];
            })
            urlParams = insertParam('origins', origins.join(), true, false, urlParams);
            const endemism = $('#endemism-filters').select2('data').map(function(data) {
                return data['text'];
            })
            urlParams = insertParam('endemism', endemism.join(), true, false, urlParams);
        } catch (e) {
        }
        const consStatus = $('#cons-status-filters').select2('data').map(function(data) {
            return data['id'];
        })
        urlParams = insertParam('cons_status', consStatus.join(), true, false, urlParams);

        for (const taxaRank of ['family', 'genus', 'species']) {
            urlParams = insertParam(taxaRank, $(`#${taxaRank}-auto-complete`).select2('data').map(function(data) {
                return data['species'] ? data['species'] : data['id'];
            }), true, false, urlParams);
        }

        const validated = $('input[name="validated"]:checked').val();
        urlParams = insertParam('validated', validated, true, false, urlParams);

        const tagFilterType = $('input[name="tag-filter-type"]:checked').val();
        urlParams = insertParam('tagFT', tagFilterType, true, false, urlParams);

        const tags = $('#tag-filters').val();
        urlParams = insertParam('tags', tags, true, false, urlParams);

        const biographicDistributions = $('#biographic-distributions-filters').val();
        urlParams = insertParam('bD', biographicDistributions, true, false, urlParams);

        const bdFilterType = $('input[name="biographic-distributions-filter-type"]:checked').val();
        urlParams = insertParam('bDFT', bdFilterType, true, false, urlParams);

        const author = $('#author-filters').val().map(a => `"${a}"`).join(',');
        urlParams = insertParam('author', encodeURIComponent(author), true, false, urlParams);

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

    function handleValidateTaxon(taxaId) {
        $('#confirmationModal').data('id', taxaId).modal('show');
    }

     function updateStatusModal(title, message, isError = false) {
        $('#statusModalLabel').text(title);
        $('#statusModalBody').text(message);
        $('#statusModal').modal('show');
        setTimeout(function() {
            $('#statusModal').modal('hide');
            if (!isError) {
                location.reload();
            }
        }, 1000); // 2 seconds timer
    }

     $('#confirmButton').click(function() {
        let id = $('#confirmationModal').data('id');
        $.ajax({
            url: approveUrl + id + '/' + selectedTaxonGroup + '/',
            headers: {"X-CSRFToken": csrfToken},
            type: 'PUT',
            data: {
                'action': 'approve'
            },
            success: function () {
                updateStatusModal('Success', 'Taxon is successfully validated.');
            },
            error: function (e) {
                updateStatusModal('Error', 'Something is wrong, please try again.', true);
                console.log(e);
            }
        });
        $('#confirmationModal').modal('hide');
    });

    function handleRejectTaxon(taxaId) {
        const modal = $('#confirmRejectModal');
        modal.find('.rejection-message').val('');
        modal.modal('show');
        modal.data('id', taxaId);
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
                updateStatusModal('Rejected', 'Taxon is successfully rejected.');
                location.reload()
            },
            error: function () {
                updateStatusModal('Error', 'Something is wrong, please try again.', true);
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

    function handleRemoveTaxonFromGroup(taxaId) {
        let r = confirm("Are you sure you want to remove this taxon from the group?");
        if (r === true) {
            removeTaxonFromTaxonGroup(taxaId);
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
        handleRemoveTaxonFromGroup,
        handleRejectTaxon,
        handleValidateTaxon
    };
})();
