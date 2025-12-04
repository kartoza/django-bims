export const addNewTaxon = (() => {
    const $newTaxonParentIdInput = $('.new-taxon-parent-id');
    const $newTaxonFamilyInput = $('.new-taxon-family-name');
    const $newTaxonParent = $('#new-taxon-parent');
    const $taxonForm = $('.new-taxon-form');
    const $addNewTaxonBtn = $taxonForm.find('.add-new-taxon-btn');
    const $newTaxonNameInput = $('#new-taxon-name');

    let selectedTaxonGroup = '';

    function showNewTaxonForm(taxonName) {
        let capitalizedTaxonName = taxonName.substr(0, 1).toUpperCase() + taxonName.substr(1).toLowerCase();
        $newTaxonNameInput.val(capitalizedTaxonName);
        $newTaxonParentIdInput.val($newTaxonParent.val());
        $taxonForm.show();
        const authorAutoComplete = $('#author-auto-complete');
        authorAutoComplete.empty();
        authorAutoComplete.val(null).trigger('change');

        $newTaxonParent.empty();
        $newTaxonParent.val(null).trigger('change');
    }

    function normalizeStatus(status) {
        const value = (status || '').toString().toUpperCase();
        return value;
    }

    function updateAcceptedLabel(status) {
        const labelEl = document.getElementById('accepted-taxon-column-label');
        const helperEl = document.getElementById('taxon-name-helper');
        if (!labelEl) return;
        const normalized = normalizeStatus(status);
        labelEl.textContent = (!normalized || normalized === 'ACCEPTED') ? 'Parent' : 'Accepted Taxon';
        if (helperEl) {
            helperEl.textContent = (!normalized || normalized === 'ACCEPTED')
                ? 'Provide the binomial name (e.g. Genus species).'
                : 'Provide the full synonym name, including genus.';
        }
    }

    function addNewTaxonToObservedList(name, gbifKey, rank, taxaId = null, parentId = "", authorName = "", taxonomicStatus = "") {
        const status = taxonomicStatus || $('#new-taxon-status').val() || '';
        const normalizedStatus = normalizeStatus(status);
        const finalStatus = normalizedStatus || 'ACCEPTED';
        let postData = {
            'gbifKey': gbifKey,
            'taxonName': name,
            'rank': rank,
            'taxonGroupId': currentSelectedTaxonGroup,
            'authorName': authorName,
            'taxonomicStatus': finalStatus,
        };
        if (parentId) {
            if (finalStatus === 'ACCEPTED') {
                postData['parentId'] = parentId;
            } else {
                postData['acceptedTaxonomyId'] = parentId;
            }
        }
        let table = $('.find-taxon-table');
        table.hide();
        let loading = $('.find-taxon-loading');
        loading.show();

        if (!taxaId) {
            $.ajax({
                url: '/api/add-new-taxon/',
                type: 'POST',
                headers: {"X-CSRFToken": csrfToken},
                data: postData,
                success: function (response) {
                    insertParam('validated', 'False', false, true);
                }
            });
            return;
        }
        $('#addNewTaxonModal').modal('toggle');
        loading.hide();
        $.ajax({
            url: '/api/add-taxa-to-taxon-group/',
            headers: {"X-CSRFToken": csrfToken},
            type: 'POST',
            data: {
                'taxaIds': JSON.stringify([taxaId]),
                'taxonGroupId': currentSelectedTaxonGroup,
            },
            success: function (response) {
                insertParam('validated', 'False', false, true);
            }
        });
    }

    function populateFindTaxonTable(table, data) {
        let tableBody = table.find('tbody');
        tableBody.html('');
        let gbifImage = '<img src="/static/img/GBIF-2015.png" width="50">';
        $.each(data, function (index, value) {
            let source = value['source'];
            let scientificName = value['scientificName'];
            let canonicalName = value['canonicalName'];
            let rank = value['rank'];
            let key = value['key'];
            let taxaId = value['taxaId'];
            let stored = value['storedLocal'];
            let validated = value['validated'];
            let taxonGroupIds = value['taxonGroupIds'];
            let status = value['status'];

            if (source === 'gbif') {
                source = `<a href="https://www.gbif.org/species/${key}" target="_blank">${gbifImage}</a>`;
                scientificName = `<a href="https://www.gbif.org/species/${key}" target="_blank">${scientificName}</a>`;
            } else if (source === 'local') {
                source = fontAwesomeIcon('database');
            }
            if (stored) {
                stored = fontAwesomeIcon('check', 'green');
                if (!validated) {
                    stored = '<span class="badge badge-secondary">Unvalidated</span>';
                }
            } else {
                stored = fontAwesomeIcon('times', 'red');
            }
            let action = '';
            const normalizedStatus = status || '';
            if (!taxonGroupIds.includes(parseInt(currentSelectedTaxonGroup))) {
                action = (`<button
                type="button"
                class="btn btn-success add-taxon-btn"
                data-canonical-name="${canonicalName}"
                data-key="${key}"
                data-rank="${rank}"
                data-status="${normalizedStatus}"
                data-taxa-id="${taxaId}">${fontAwesomeIcon('plus')}&nbsp;ADD
               </button>`);
            }
            tableBody.append(`<tr>
                    <td>${scientificName}</td>
                    <td>${canonicalName}</td>
                    <td>${rank}</td>
                    <td>${source}</td>
                    <td>${status}</td>
                    <td>${stored}</td>
                    <td>${action}</td>
                </tr>`);
        });
        table.show();
    }

    function handleFindTaxonButton(event) {
        let taxonName = $('#add-taxon-input').val();
        if (!taxonName) {
            return false;
        }
        let table = $('.find-taxon-table');
        table.hide();
        let loading = $('.find-taxon-loading');
        loading.show();
        $taxonForm.hide();

        $.ajax({
            url: `/api/find-taxon/?q=${encodeURIComponent(taxonName)}&taxonGroupId=${currentSelectedTaxonGroup}`,
            type: 'get',
            dataType: 'json',
            success: function (data) {
                if (data.length > 0) {
                    populateFindTaxonTable(table, data);
                } else {
                    showNewTaxonForm(taxonName);
                }
                loading.hide();
            }
        });
    }

    function handleAddNewTaxon(event) {
        let $rank = $taxonForm.find('.new-taxon-rank');
        let $author = $taxonForm.find('#author-auto-complete');
        const status = $('#new-taxon-status').val();
        const parentId = $newTaxonParent.val();
        if (!parentId) {
            if (status.toLowerCase() === 'accepted') {
                alert("Missing parent");
            } else {
                alert("Missing accepted taxon");
            }
            return;
        }
        addNewTaxonToObservedList($newTaxonNameInput.val(), '', $rank.val(), null, parentId, $author.val(), status);
        $taxonForm.hide();
        $newTaxonFamilyInput.val("");
        $newTaxonParentIdInput.val("");
    }

    function clearForm() {
        $('#add-taxon-input').val('');

        const table = $('.find-taxon-table');
        table.hide();
        table.find('tbody').empty();

        $('.find-taxon-loading').hide();

        $taxonForm.show();
        $newTaxonNameInput.val('');
        $newTaxonFamilyInput.val('');
        $newTaxonParentIdInput.val('');

        $newTaxonParent.empty();
        $newTaxonParent.val(null).trigger('change');

        const authorAutoComplete = $('.author-auto-complete');
        authorAutoComplete.val(null).trigger('change');
    }

    function init(_selectedTaxonGroup) {

        $('#addNewTaxonModal').on('shown.bs.modal', function (e) {
            const authorAutoComplete = $('#author-auto-complete');
            authorAutoComplete.empty();
            authorAutoComplete.val(null).trigger('change');

            $newTaxonParent.empty();
            $newTaxonParent.val(null).trigger('change');
            updateAcceptedLabel($('#new-taxon-status').val());
        });

        $('#addNewTaxonModal').on('hidden.bs.modal', function () {
            clearForm();
        });

        selectedTaxonGroup = _selectedTaxonGroup;

        $('#find-taxon-button').on('click', handleFindTaxonButton);
        $addNewTaxonBtn.on('click', handleAddNewTaxon);

        $(document).on('click', '.add-taxon-btn', function() {
            const button = $(this);
            const name = button.data('canonical-name');
            const gbifKey = button.data('key');
            const rank = button.data('rank');
            const taxaId = button.data('taxa-id');
            const status = button.data('status') || '';
            addNewTaxonToObservedList(name, gbifKey, rank, taxaId, "", "", status);
        });

        $('#new-taxon-status').on('change', function () {
            updateAcceptedLabel(this.value);
        });

        updateAcceptedLabel($('#new-taxon-status').val());

        const authorAutoComplete = $('.author-auto-complete');
        authorAutoComplete.select2({
            width: '100%',
            ajax: {
                url: '/author-autocomplete/',
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        term: params.term,
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.map(item => {
                            return {
                                id: item.author,
                                text: item.author
                            };
                        }),
                    };
                },
                cache: true
            },
            allowClear: true,
            placeholder: 'Search for an Author',
            minimumInputLength: 3,
            templateResult: (item) => item.text,
            templateSelection: (item) => item.text,
            tags: true,
            createTag: function (params) {
                if (!this.$element.data('add-new-tag')) {
                    return null;
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
    }

    return {
        init,
        clear: clearForm,
    }
})()
