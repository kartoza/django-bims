// ----- Global variables ----- //
let taxaListCurrentUrl = '';
let selectedTaxonGroup = '';
let urlDownload = '/download-csv-taxa-list/';
let taxonGroupUpdateOrderUrl = '/api/update-taxon-group-order/';
let removeTaxaFromTaxonGroupUrl = '/api/remove-taxa-from-taxon-group/';

// ----- Global elements ----- //
let $sortable = $('#sortable');
let $searchButton = $('#search-button');
let $downloadCsvButton = $('#download-csv');
let $loadingOverlay = $('.loading');
let $removeTaxonFromGroupBtn = $('.remove-taxon-from-group');

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
            headers:{ "X-CSRFToken": csrfToken },
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
    getTaxaList(`/api/taxa-list/?taxonGroup=${selectedTaxonGroup}&taxon=${taxonName}`);
});

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
    let $target = $(e.target);
    let $taxonGroupCard = $(`#taxon_group_${selectedTaxonGroup}`);
    let maxTry = 10;
    let currentTry = 0;
    while (!$target.hasClass('taxa-row') && currentTry < maxTry) {
        currentTry += 1;
        $target = $target.parent();
    }
    let id = $target.data('id');
    let currentTaxonomiesCount = parseInt($taxonGroupCard.html());
    showLoading();
        $.ajax({
            url: removeTaxaFromTaxonGroupUrl,
            headers:{ "X-CSRFToken": csrfToken },
            type: 'POST',
            data: {
                'taxaIds': JSON.stringify([id]),
                'taxonGroupId': selectedTaxonGroup
            },
            success: function (response) {
                hideLoading();
                $taxonGroupCard.html(response['taxonomy_count']);
                getTaxaList(taxaListCurrentUrl);
            }
    });
});

// ----- Functions ----- //
const getTaxaList = (url) => {
    taxaListCurrentUrl = url;
    showLoading();
    $('.download-button-container').show();
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

$('.ui-state-default').click(function (e) {
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
    getTaxaList(`/api/taxa-list/?taxonGroup=${selectedTaxonGroup}`);
})


$('#find-taxon-button').click(function () {
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

function windowpop(url, width, height) {
    let leftPosition, topPosition;
    // Allow for borders.
    leftPosition = (window.screen.width / 2) - ((width / 2) + 10);
    // Allow for title and status bars.
    topPosition = (window.screen.height / 2) - ((height / 2) + 50);
    // Open the window.
    window.open(url, "Window2", "status=no,height=" + height + ",width=" + width + ",resizable=yes,left=" + leftPosition + ",top=" + topPosition + ",screenX=" + leftPosition + ",screenY=" + topPosition + ",toolbar=no,menubar=no,scrollbars=no,location=no,directories=no");
}

function showNewTaxonForm(taxonName) {
    let $taxonForm = $('.new-taxon-form');
    let $button = $taxonForm.find('.add-new-taxon-btn');
    let $rank = $taxonForm.find('.new-taxon-rank');
    let capitalizedTaxonName = taxonName.substr(0, 1).toUpperCase() + taxonName.substr(1).toLowerCase();
    let $newTaxonNameInput = $('#new-taxon-name');
    $button.click(function () {
        $taxonForm.hide();
        addNewTaxonToObservedList(capitalizedTaxonName, '', $rank.val());
    });
    $newTaxonNameInput.val(capitalizedTaxonName);
    $taxonForm.show();
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

function addNewTaxonToObservedList(name, gbifKey, rank, taxaId = null) {
    let postData = {
        'gbifKey': gbifKey,
        'taxonName': name,
        'rank': rank,
        'taxonGroup': taxonGroupName,
        'csrfmiddlewaretoken': csrfToken
    };
    let table = $('.find-taxon-table');
    table.hide();
    let loading = $('.find-taxon-loading');
    loading.show();

    if (taxaId) {
        $('#addNewTaxonModal').modal('toggle');
        loading.hide();
        $('#add-taxon-input').val('');

        if (taxaIdList.indexOf(taxaId + '') === -1) {
            renderNewTaxon(taxaId, name);
        } else {
            let div = $('.taxon-table-body').find(`.taxon-id[value="${taxaId}"]`);
            if (div.length) {
                div = div.parent().parent();
                div.scrollHere();
                div.highlight();
            }
        }
        return true;
    }

    $.ajax({
        url: `/api/add-new-taxon/`,
        type: 'POST',
        data: postData,
        success: function (data) {
            $('#addNewTaxonModal').modal('toggle');
            renderNewTaxon(data['id'], name);
            loading.hide();
            $('#add-taxon-input').val('');
        }
    });
}

// Add new taxon row to the existing taxa list
function renderNewTaxon(taxonId, taxonName) {
    let $container = $('.taxon-table-body');
    taxaIdList.push(taxonId + '');
    let $row = $('<tr>');
    $row.html(
        '<td scope="row" class="taxon-name">' +
        taxonName +
        '<input type="hidden" class="taxon-id" value="' + taxonId + '">' +
        '</td>');
    $row.append(
        '<td>' +
        '<div class="form-check">' +
        '<input class="form-check-input observed" type="checkbox"' +
        ' value="True"' +
        ' name="' + taxonId + '-observed">' +
        ' <label class="form-check-label">' +
        ' </label>' +
        '</div>' +
        '</td>');
    let taxonAbundanceInput = $('<input type="number" min="0"' +
        ' name="' + taxonId + '-abundance"' +
        ' class="form-control taxon-abundance"' +
        ' placeholder="0">');
    let tdTaxonAbundance = $('<td>');
    tdTaxonAbundance.append(taxonAbundanceInput);
    $row.append(tdTaxonAbundance);
    $container.prepend($row);
    $row.scrollHere();
    $row.highlight();
    taxonAbundanceInput.change(taxonAbundanceOnChange);
}

hideLoading();