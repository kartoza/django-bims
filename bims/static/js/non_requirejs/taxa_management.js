// ----- Global variables ----- //
let taxaListCurrentUrl = '';
let selectedTaxonGroup = '';
let urlDownload = '/download-csv-taxa-list/';
let taxonGroupUpdateOrderUrl = '/api/update-taxon-group-order/';
let removeTaxaFromTaxonGroupUrl = '/api/remove-taxa-from-taxon-group/';
let addTaxaToTaxonGroupUrl = '/api/add-taxa-to-taxon-group/';
let addNewTaxonUrl = '/api/add-new-taxon/';

// ----- Global elements ----- //
let $sortable = $('#sortable');
let $searchButton = $('#search-button');
let $downloadCsvButton = $('#download-csv');
let $loadingOverlay = $('.loading');
let $removeTaxonFromGroupBtn = $('.remove-taxon-from-group');
let $taxonGroupCard = $('.ui-state-default');
let $findTaxonButton = $('#find-taxon-button');
let $updateLogoBtn = $('.update-logo-btn');
let $removeAllBtn = $('.remove-all-btn');
let $clearSearchBtn = $('#clear-search-button');
let $sortBtn = $('.sort-button');

// ----- Bind element to events ----- //
$sortable.sortable({
    stop: function (event, ui) {
        let $li = $(event.target).find('li');
        let ids = [];
        $.each($li, function (index, element) {
            ids.push($(element).data('id'));
        });
        $sortable.sortable("disable");
        showLoading();
        $.ajax({
            url: taxonGroupUpdateOrderUrl,
            headers: {"X-CSRFToken": csrfToken},
            type: 'POST',
            data: {
                'taxonGroups': JSON.stringify(ids)
            },
            success: function (response) {
                hideLoading();
                $sortable.sortable("enable");
            }
        });
    }
});

$searchButton.click(function (e) {
    if (!taxaListCurrentUrl) {
        return true;
    }
    let taxonNameInput = $('#taxon-name-input');
    let taxonName = taxonNameInput.val();
    insertParam('taxon', taxonName);
});

$clearSearchBtn.click(function (e) {
     insertParam('taxon', '');
});

$sortBtn.click(function (event) {
    let $target = $(event.target);
    let order = $target.data('order');
    if (order) {
        insertParam('o', order);
    }
})

$downloadCsvButton.click(function (e) {
    let a = document.createElement("a");
    let url = urlDownload + '?taxonGroup=' + selectedTaxonGroup;
    let taxonName = $('#taxon-name-input').val();
    if (taxonName) {
        url += '&taxon=' + taxonName;
    }
    a.href = url;
    a.download = 'taxa-list.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(urlDownload);
    a.remove();
});

$removeTaxonFromGroupBtn.click(function (e) {
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
});

$taxonGroupCard.click(function (e) {
    let $elm = $(e.target);
    let maxTry = 10;
    let currentTry = 1;
    while (!$elm.hasClass('ui-state-default') && currentTry < maxTry) {
        currentTry++;
        $elm = $elm.parent();
    }
    $('.ui-state-default').removeClass('selected');
    $elm.addClass('selected');
    selectedTaxonGroup = $elm.data('id');
    $('#taxon-name-input').val('');
    insertParam('selected', selectedTaxonGroup);
})

$findTaxonButton.click(function () {
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
        url: `/api/find-taxon/?q=${taxonName}&status=accepted&taxonGroup=fish`,
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
});

const $removeModuleName = $('#remove-module-name');
const $removeModuleBtn = $('#remove-module-btn');
let currentRemoveModuleName = '-';
$removeModuleName.on('input', (e) => {
    if ($removeModuleName.val() === currentRemoveModuleName) {
        $removeModuleBtn.attr('disabled', false);
    } else {
        $removeModuleBtn.attr('disabled', true);
    }
});

$removeAllBtn.click((event) => {
    event.preventDefault();
    $removeModuleBtn.attr('disabled', true);
    const _maxTries = 10;
    let _element = $(event.target);
    let _currentTry = 1
    while (!_element.hasClass('ui-sortable-handle') && _currentTry < _maxTries) {
        _element = _element.parent();
        _currentTry += 1;
    }
    currentRemoveModuleName = _element.find('.taxon-group-title').html().trim();
    $removeModuleName.val('');
    $('#remove-module-btn').attr('data-module-id', _element.data('id'));
    $('#removeModuleModal').modal({
        keyboard: false
    })
    return false;
});

$removeModuleBtn.click((e) => {
    e.preventDefault();
    $removeModuleBtn.html('Processing...')
    $removeModuleBtn.attr('disabled', true)
    const moduleId = $(e.target).data('module-id');
    const url = `/api/remove-occurrences/?taxon_module=${moduleId}`
    $.ajax({
        type: 'GET',
        headers: {"X-CSRFToken": csrfToken},
        url: url,
        cache: false,
        contentType: false,
        processData: false,
        success: function () {
            location.reload();
        },
        error: function (data) {
            console.log("error");
            console.log(data);
        }
    });
})

$updateLogoBtn.click((event) => {
    event.preventDefault();
    const _maxTries = 10;
    let _element = $(event.target);
    let _currentTry = 1
    while (!_element.hasClass('ui-sortable-handle') && _currentTry < _maxTries) {
        _element = _element.parent();
        _currentTry += 1;
    }
    const moduleName = _element.find('.taxon-group-title').html().trim();
    $('#edit-module-img-container').html(
        `<img style="max-width: 100%" src=${_element.find('img').attr('src')}>`
    )
    $('#edit-module-name').val(moduleName);
    $('#edit-module-id').val(_element.data('id'));
    $('#editModuleModal').modal({
        keyboard: false
    })
    return false;
});

$('#moduleRemoveForm').on('submit', function (e) {
    e.preventDefault();
    let formData = new FormData(this);
    let url = '/api/delete-taxon-group/';
    $.ajax({
        type: 'POST',
        headers: {"X-CSRFToken": csrfToken},
        url: url,
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        success: function (data) {
            location.reload();
        },
        error: function (data) {
            console.log("error");
            console.log(data);
        }
    });
})

$('#moduleEditForm').on('submit', function (e) {
    e.preventDefault();
    let formData = new FormData(this);
    let url = '/api/update-taxon-group/';
    $.ajax({
        type: 'POST',
        headers: {"X-CSRFToken": csrfToken},
        url: url,
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        success: function (data) {
            location.reload();
        },
        error: function (data) {
            console.log("error");
            console.log(data);
        }
    });
})

// ----- Functions ----- //
const getTaxaList = (url) => {
    taxaListCurrentUrl = url;
    showLoading();
    $('.download-button-container').show();
    console.log(url)
    $.get(url).then(
        function (response) {
            hideLoading();
            let $taxaList = $('#taxa-list');
            let $pagination = $('.pagination-centered');
            let paginationNext = $('.pagination-next');
            let paginationPrev = $('.pagination-previous');

            // Get current page by parsing the next url
            let currentPage = 1;
            let taxaCurrentSize = 0;
            if (response['next']) {
                let url = new URL(response['next']);
                let page = url.searchParams.get('page');
                currentPage = page - 1;
                taxaCurrentSize = currentPage * 20;
            }
            if (!response['next'] && response['previous']) {
                let url = new URL(response['previous']);
                currentPage = parseInt(url.searchParams.get('page')) + 1;
                taxaCurrentSize = response['count']
            }
            $taxaList.html('');
            $.each(response['results'], function (index, data) {
                let name = data['canonical_name'];
                if (!name) {
                    name = data['scientific_name'];
                }
                let $rowAction = $('.row-action').clone(true, true);
                $rowAction.removeClass('row-action');
                $rowAction.show();
                let $row = $(`<tr class="taxa-row" data-id="${data['id']}"></tr>`);
                $taxaList.append($row);
                $row.append(`<td>${name}</td>`);
                $row.append(`<td>${data['rank']}</td>`);
                $row.append(`<td>${data['origin_name']}</td>`);
                $row.append(`<td>${data['endemism_name']}</td>`);
                $row.append(`<td>${data['import_date']}</td>`);
                let $tdAction = $(`<td></td>`);
                $row.append($tdAction);
                $tdAction.append($rowAction);
                $rowAction.find('.edit-taxon').click((event) => event.preventDefault());
                $rowAction.find('.edit-taxon').attr('href', `/admin/bims/taxonomy/${data['id']}/change/?_popup=1`);
            });
            if (response['next'] == null && response['previous'] == null) {
                $pagination.hide();
            } else {
                $('#taxa-count').html(response['count']);
                $('#taxa-current-size').html(taxaCurrentSize);
                $('#taxa-current-page').html((currentPage * 20) - 19);
                $pagination.show();
                if (response['next']) {
                    paginationNext.show();
                    paginationNext.off('click');
                    paginationNext.click(() => {
                        getTaxaList(response['next']);
                    })
                } else {
                    paginationNext.hide();
                }
                if (response['previous']) {
                    paginationPrev.show();
                    paginationPrev.off('click');
                    paginationPrev.click(() => {
                        getTaxaList(response['previous']);
                    })
                } else {
                    paginationPrev.hide();
                }
            }
        }
    )
}

const showLoading = () => {
    $loadingOverlay.show();
}

const hideLoading = () => {
    $loadingOverlay.hide();
}

function windowpop(url, width, height) {
    let leftPosition, topPosition;
    // Allow for borders.
    leftPosition = (window.screen.width / 2) - ((width / 2) + 10);
    // Allow for title and status bars.
    topPosition = (window.screen.height / 2) - ((height / 2) + 50);
    // Open the window.
    window.open(url, "Window2", "status=no,height=" + height + ",width=" + width + ",resizable=yes,left=" + leftPosition + ",top=" + topPosition + ",screenX=" + leftPosition + ",screenY=" + topPosition + ",toolbar=no,menubar=no,scrollbars=no,location=no,directories=no");
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

        if (source === 'gbif') {
            source = `<a href="https://www.gbif.org/species/${key}" target="_blank">${gbifImage}</a>`;
            scientificName = `<a href="https://www.gbif.org/species/${key}" target="_blank">${scientificName}</a>`;
        } else if (source === 'local') {
            source = fontAwesomeIcon('database');
        }
        if (stored) {
            stored = fontAwesomeIcon('check', 'green');
        } else {
            stored = fontAwesomeIcon('times', 'red');
        }
        let action = (`<button
                        type="button"
                        onclick="addNewTaxonToObservedList('${canonicalName}',${key},'${rank}',${taxaId})"
                        class="btn btn-success">${fontAwesomeIcon('plus')}&nbsp;ADD
                       </button>`);
        tableBody.append(`<tr>
                    <td>${scientificName}</td>
                    <td>${canonicalName}</td>
                    <td>${rank}</td>
                    <td>${source}</td>
                    <td>${stored}</td>
                    <td>${action}</td>
                </tr>`);
    });
    table.show();
}

function addNewTaxonToObservedList(name, gbifKey, rank, taxaId = null, familyId = "") {
    let postData = {
        'gbifKey': gbifKey,
        'taxonName': name,
        'rank': rank
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
            url: addNewTaxonUrl,
            type: 'POST',
            headers: {"X-CSRFToken": csrfToken},
            data: postData,
            success: function (response) {
                $('#addNewTaxonModal').modal('toggle');
                loading.hide();
                $('#add-taxon-input').val('');
                addNewTaxonToObservedList(
                    name,
                    gbifKey,
                    rank,
                    response['id']
                )
            }
        });
        return
    }

    let $taxonGroupCard = $(`#taxon_group_${selectedTaxonGroup}`);
    $('#addNewTaxonModal').modal('toggle');
    loading.hide();
    showLoading();
    $.ajax({
        url: addTaxaToTaxonGroupUrl,
        headers: {"X-CSRFToken": csrfToken},
        type: 'POST',
        data: {
            'taxaIds': JSON.stringify([taxaId]),
            'taxonGroupId': selectedTaxonGroup,
        },
        success: function (response) {
            $taxonGroupCard.html(response['taxonomy_count']);
            getTaxaList(taxaListCurrentUrl);
        }
    });
}

function removeTaxonFromTaxonGroup(taxaId) {
    let $taxonGroupCard = $(`#taxon_group_${selectedTaxonGroup}`);
    showLoading();
    $.ajax({
        url: removeTaxaFromTaxonGroupUrl,
        headers: {"X-CSRFToken": csrfToken},
        type: 'POST',
        data: {
            'taxaIds': JSON.stringify([taxaId]),
            'taxonGroupId': selectedTaxonGroup
        },
        success: function (response) {
            hideLoading();
            $taxonGroupCard.html(response['taxonomy_count']);
            getTaxaList(taxaListCurrentUrl);
        }
    });
}

const $newTaxonFamilyIdInput = $('.new-taxon-family-id');
const $newTaxonFamilyInput = $('.new-taxon-family-name');
const $taxonForm = $('.new-taxon-form');
const $button = $taxonForm.find('.add-new-taxon-btn');
const $newTaxonNameInput = $('#new-taxon-name');

function showNewTaxonForm(taxonName) {
    let capitalizedTaxonName = taxonName.substr(0, 1).toUpperCase() + taxonName.substr(1).toLowerCase();
    speciesAutoComplete($newTaxonFamilyInput, '&rank=family').then(value => {
        $newTaxonFamilyIdInput.val(value);
    })
    $newTaxonNameInput.val(capitalizedTaxonName);
    $taxonForm.show();
}

$button.click(function () {
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
});

$(document).ready(function () {
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    let url = ''
    let taxonName = ''
    if (urlParams.get('selected')) {
        selectedTaxonGroup = urlParams.get('selected');
        $('#sortable').find(`[data-id="${selectedTaxonGroup}"]`).addClass('selected');
        url = `/api/taxa-list/?taxonGroup=${selectedTaxonGroup}`
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
    if (url) {
        getTaxaList(url);
    }
});


hideLoading();