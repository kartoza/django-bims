export const addNewTaxon = (() => {
    const $newTaxonFamilyIdInput = $('.new-taxon-family-id');
    const $newTaxonFamilyInput = $('.new-taxon-family-name');
    const $taxonForm = $('.new-taxon-form');
    const $addNewTaxonBtn = $taxonForm.find('.add-new-taxon-btn');
    const $newTaxonNameInput = $('#new-taxon-name');

    let selectedTaxonGroup = '';

    function showNewTaxonForm(taxonName) {
        let capitalizedTaxonName = taxonName.substr(0, 1).toUpperCase() + taxonName.substr(1).toLowerCase();
        speciesAutoComplete($newTaxonFamilyInput, '&rank=family').then(value => {
            $newTaxonFamilyIdInput.val(value);
        })
        $newTaxonNameInput.val(capitalizedTaxonName);
        $taxonForm.show();
    }

    function addNewTaxonToObservedList(name, gbifKey, rank, taxaId = null, familyId = "") {
        let postData = {
            'gbifKey': gbifKey,
            'taxonName': name,
            'rank': rank,
            'taxonGroupId': selectedTaxonGroup
        };
        if (familyId) {
            postData['familyId'] = familyId
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
            return
        }
        $('#addNewTaxonModal').modal('toggle');
        loading.hide();
        $.ajax({
            url: '/api/add-taxa-to-taxon-group/',
            headers: {"X-CSRFToken": csrfToken},
            type: 'POST',
            data: {
                'taxaIds': JSON.stringify([taxaId]),
                'taxonGroupId': selectedTaxonGroup,
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
                    stored = '<span class="badge badge-secondary">Unvalidated</span>'
                }
            } else {
                stored = fontAwesomeIcon('times', 'red');
            }
            let action = '';
            if (!taxonGroupIds.includes(parseInt(selectedTaxonGroup))) {
                action = (`<button
                type="button"
                class="btn btn-success add-taxon-btn"
                data-canonical-name="${canonicalName}"
                data-key="${key}"
                data-rank="${rank}"
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
        // Show loading div
        let table = $('.find-taxon-table');
        table.hide();
        let loading = $('.find-taxon-loading');
        loading.show();
        let $newTaxonForm = $('.new-taxon-form');
        $newTaxonForm.hide();

        // Show response list
        $.ajax({
            url: `/api/find-taxon/?q=${encodeURIComponent(taxonName)}&taxonGroupId=${selectedTaxonGroup}`,
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
        const familyId = $newTaxonFamilyIdInput.val();
        if (!familyId) {
            alert("Missing family");
            return
        }
        addNewTaxonToObservedList($newTaxonNameInput.val(), '', $rank.val(), null, familyId);
        $taxonForm.hide();
        $newTaxonFamilyInput.val("")
        $newTaxonFamilyIdInput.val("")
    }

    function init(_selectedTaxonGroup) {
        selectedTaxonGroup = _selectedTaxonGroup

        $('#find-taxon-button').on('click', handleFindTaxonButton)
        $addNewTaxonBtn.on('click', handleAddNewTaxon)

        $(document).on('click', '.add-taxon-btn', function() {
            const button = $(this); // The clicked button
            const name = button.data('canonical-name');
            const gbifKey = button.data('key');
            const rank = button.data('rank');
            const taxaId = button.data('taxa-id');
            addNewTaxonToObservedList(name, gbifKey, rank, taxaId);
        });
    }

    return {
        init,
    }
})()
