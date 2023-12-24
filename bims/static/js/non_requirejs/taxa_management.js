// ----- Global variables ----- //
let taxaListCurrentUrl = '';
let selectedTaxonGroup = '';
let urlDownload = '/download-csv-taxa-list/';
let taxonGroupUpdateOrderUrl = '/api/update-taxon-group-order/';
let removeTaxaFromTaxonGroupUrl = '/api/remove-taxa-from-taxon-group/';
let addTaxaToTaxonGroupUrl = '/api/add-taxa-to-taxon-group/';
let addNewTaxonUrl = '/api/add-new-taxon/';
let filterSelected = {};

// ----- Global elements ----- //
let $sortable = $('#sortable');
let $searchButton = $('#search-button');
let $downloadCsvButton = $('#download-csv');
let $loadingOverlay = $('.loading');
let $removeTaxonFromGroupBtn = $('.remove-taxon-from-group');
let $validateTaxonBtn = $('.validate-taxon');
let $rejectTaxonBtn = $('.reject-taxon');
let $taxonGroupCard = $('.ui-state-default');
let $findTaxonButton = $('#find-taxon-button');
let $updateLogoBtn = $('.update-logo-btn');
let $removeAllBtn = $('.remove-all-btn');
let $clearSearchBtn = $('#clear-search-button');
let $sortBtn = $('.sort-button');
let $addAttributeBtn = $('.btn-add-extra-attribute');

const popupCenter = ({url, title, w, h}) => {
    // Fixes dual-screen position                             Most browsers      Firefox
    const dualScreenLeft = window.screenLeft !==  undefined ? window.screenLeft : window.screenX;
    const dualScreenTop = window.screenTop !==  undefined   ? window.screenTop  : window.screenY;

    const width = window.innerWidth ? window.innerWidth : document.documentElement.clientWidth ? document.documentElement.clientWidth : screen.width;
    const height = window.innerHeight ? window.innerHeight : document.documentElement.clientHeight ? document.documentElement.clientHeight : screen.height;

    const systemZoom = width / window.screen.availWidth;
    const left = (width - w) / 2 / systemZoom + dualScreenLeft
    const top = (height - h) / 2 / systemZoom + dualScreenTop
    const newWindow = window.open(url, title,
      `
      scrollbars=yes,
      width=${w / systemZoom}, 
      height=${h / systemZoom}, 
      top=${top}, 
      left=${left}
      `
    )

    if (window.focus) newWindow.focus();
}

// ----- Bind element to events ----- //
if (userCanEditTaxonGroup) {
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
}

$searchButton.click(function (e) {
    if (!taxaListCurrentUrl) {
        return true;
    }
    let taxonNameInput = $('#taxon-name-input');
    let taxonName = taxonNameInput.val();
    insertParam('taxon', taxonName);
});

$clearSearchBtn.click(function (e) {
    let urlParams = document.location.search.substr(1);
    if (Object.keys(filterSelected).length > 0) {
        $.each(filterSelected, function (key, value) {
            urlParams = insertParam(key, '', true, false, urlParams);
        })
    }
    urlParams = insertParam('taxon', '', true, false, urlParams);
    document.location.search = urlParams;
});

$sortBtn.click(function (event) {
    let $target = $(event.target);
    let order = $target.data('order');
    if (order) {
        insertParam('o', order);
    }
})

$downloadCsvButton.click(function (e) {
    const $target = $(e.target);
    const targetHtml = $target.html();
    const targetWidth = $target.width();
    const _downloadMessage = 'Your data download is underway. ' +
            'This may take some time. ' +
            'You will be notified by email when your download is ready. ' +
            'Thank you for your patience.';
    $target.prop('disabled', true);
    $target.html(`<div style="width: ${targetWidth}px;"><img src="/static/images/default/grid/loading.gif" width="20"/></div>`);
    fetch(taxaListCurrentUrl.replace('/api/taxa-list/', urlDownload))
        .then((resp) => {
            $target.prop('disabled', false);
            $target.html(targetHtml);
            alert(_downloadMessage);
        })
        .catch(() => alert('Cannot download the file'));
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

$validateTaxonBtn.click(function (e) {
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
            url: approveUrl,
            data: {
                'pk': id
            },
            success: function () {
                alert('Taxon is successfully validated.');
                location.reload()
            },
            error: function () {
                alert('Something is wrong, please try again.');
                location.reload()
            }
        })
    }
});

$rejectTaxonBtn.click(function (e) {
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
});

$('#rejectBtn').click(function () {
    const modal = $('#confirmRejectModal');
    const id = modal.data('id');
    const rejectionMessage = modal.find('.rejection-message').val();
    $.ajax({
        url: rejectUrl,
        data: {
            'pk': id,
            'rejection_message': rejectionMessage
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

removeExtraAttribute = (event) => {
    event.preventDefault();
    $(event.target).parent().remove();
}

function findExpertsByTaxonGroupId(parentId) {
    let experts = [];
    taxaGroups.forEach(item => {
        if (item.id === parentId && item.experts.length > 0) {
            experts = experts.concat(item.experts);
        }
    });
    return experts;
}

function addExpertsToSelect(experts) {
    let expertIds = [];
    experts.forEach(expert => {
        let newOption = new Option(expert.full_name, expert.id, false, false);
        authorSelect.append(newOption);
        expertIds.push(expert.id);
    });
    authorSelect.val(expertIds);
    authorSelect.trigger('change');
}

$updateLogoBtn.click((event) => {
    event.preventDefault();
    const _maxTries = 10;
    let _element = $(event.target);
    let _currentTry = 1
    while (!_element.hasClass('ui-sortable-handle') && _currentTry < _maxTries) {
        _element = _element.parent();
        _currentTry += 1;
    }
    const moduleId = _element.data('id');
    const moduleName = _element.find('.taxon-group-title').html().trim();
    const extraAttributesContainer = $('#editModuleModal').find('.extra-attribute-field');
    let extraAttributes = _element.find('.taxon-group-title').data('extra-attributes');
    extraAttributesContainer.html('')
    if (extraAttributes.length > 0) {
        extraAttributes = JSON.parse(extraAttributes.replace(/'/g, '"'));
        for (let i=0; i<extraAttributes.length; i++) {
            let exAtEl = '<div style="display: flex" >' +
                    '<input aria-label="extra-attribute" type="text" class="form-control" name="extra_attribute" value="' + extraAttributes[i] + '" />' +
                    '<button class="btn btn-danger remove-extra-attribute" onclick="removeExtraAttribute(event)">-</button>'
                '</div>';
            extraAttributesContainer.append(exAtEl);
        }
    }
    let imgElement = _element.find('img');

    if (imgElement.length > 0 && imgElement.attr('src')) {
        $('#edit-module-img-container').html(
            `<img style="max-width: 100%" src="${imgElement.attr('src')}">`
        );
    } else {
        $('#edit-module-img-container').html('');
    }
    $('#edit-module-name').val(moduleName);
    $('#edit-module-id').val(_element.data('id'));
    $('#editModuleModal').modal({
        keyboard: false
    })

    // Experts
    authorSelect.empty();
    authorSelect.val(null).trigger('change');
    let experts = findExpertsByTaxonGroupId(moduleId);
    addExpertsToSelect(experts);

    return false;
});

$addAttributeBtn.click((event) => {
    event.preventDefault();

    const extraAttributesContainer = $('#editModuleModal').find('.extra-attribute-field');
    let exAtEl = '<div style="display: flex" >' +
                    '<input aria-label="extra-attribute" type="text" class="form-control" name="extra_attribute" value="" />' +
                    '<button class="btn btn-danger remove-extra-attribute" onclick="removeExtraAttribute(event)">-</button>'
                '</div>';
    extraAttributesContainer.append(exAtEl);

})

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
    formData.delete('taxon-group-experts');

    $('.owner-auto-complete').select2('data').forEach(function(item) {
        formData.append('taxon-group-experts', item.id);
    });

    let url = '/api/update-taxon-group/';
    $(e.target).find('.btn-submit').prop('disabled', true);
    $(e.target).find('.loading-btn').show();
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
    $.get(url).then(
        function (response) {
            hideLoading();
            $('#total-taxa').html(response.count);
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
                let searchUrl = `/map/#search/${name}/taxon=&search=${name}&sourceCollection=${JSON.stringify(sourceCollection)}`;
                name += `<br/><span style="font-size: 9pt">${data['scientific_name']}</span><br/>`;
                if (data['common_name']) {
                    name += ` <span class="badge badge-info">${data['common_name']}</span><br/>`
                }
                if (data['gbif_key'] || data['iucn_redlist_id']) {
                    name += '<div style="border-top: 1px solid black; margin-top: 5px; margin-bottom: 5px;"></div>';
                }
                if (data['gbif_key']) {
                    name += ` <a href="https://www.gbif.org/species/${data['gbif_key']}" target="_blank"><span class="badge badge-warning">GBIF</span></a>`
                }
                if (data['iucn_redlist_id']) {
                    name += ` <a href="https://apiv3.iucnredlist.org/api/v3/taxonredirect/${data['iucn_redlist_id']}/" target="_blank"><span class="badge badge-danger">IUCN</span></a>`
                }
                if (!data['validated']) {
                    name += '<br/><span class="badge badge-secondary">Unvalidated</span></a>';
                }
                let $rowAction = $('.row-action').clone(true, true);
                if (userCanEditTaxon) {
                    $rowAction.removeClass('row-action');
                    if (!data['validated']) {
                        $rowAction.find('.btn-validated-container').hide();
                        $rowAction.find('.btn-unvalidated-container').show();
                    } else {
                        $rowAction.find('.btn-validated-container').show();
                        $rowAction.find('.btn-unvalidated-container').hide();
                    }
                    $rowAction.show();
                }
                let $row = $(`<tr class="taxa-row" data-id="${data['id']}"></tr>`);
                $taxaList.append($row);
                $row.append(`<td>${name}</td>`);
                $row.append(`<td>${data['rank']}</td>`);
                $row.append(`<td>${data['iucn_status_full_name']}</td>`);
                $row.append(`<td>${data['origin_name']}</td>`);
                $row.append(`<td>${data['endemism_name']}</td>`);
                $row.append(`<td>${data['total_records']}&nbsp;<a href='${searchUrl}' target="_blank"><i class="fa fa-search" aria-hidden="true"></i></a></td>`);
                $row.append(`<td>${data['import_date']}</td>`);

                if (userCanEditTaxon) {
                    let $tdAction = $(`<td style="width: 170px;"></td>`);
                    $row.append($tdAction);
                    $tdAction.append($rowAction);
                    $rowAction.find('.edit-taxon').click((event) => {
                        event.preventDefault();
                        popupCenter({url: `/admin/bims/taxonomy/${data['id']}/change/?_popup=1`, title: 'xtf', w: 900, h: 500});
                        return false;
                    });
                }
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
                        const urlParams = new URLSearchParams(new URL(response['next']).search);
                        insertParam('page', urlParams.get('page'), false);
                    })
                } else {
                    paginationNext.hide();
                }
                if (response['previous']) {
                    paginationPrev.show();
                    paginationPrev.off('click');
                    paginationPrev.click(() => {
                        const urlParams = new URLSearchParams(new URL(response['previous']).search);
                        insertParam('page', urlParams.get('page'), false);
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
                onclick="addNewTaxonToObservedList('${canonicalName}',${key},'${rank}',${taxaId})"
                class="btn btn-success">${fontAwesomeIcon('plus')}&nbsp;ADD
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
            url: addNewTaxonUrl,
            type: 'POST',
            headers: {"X-CSRFToken": csrfToken},
            data: postData,
            success: function (response) {
                $('#addNewTaxonModal').modal('toggle');
                loading.hide();
                $('#add-taxon-input').val('');
                getTaxaList(taxaListCurrentUrl);
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
const $applyFiltersBtn = $('#apply-filters');

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

$applyFiltersBtn.click(function () {
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

    document.location.search = urlParams;
})

$('#collapseFilter').on('shown.bs.collapse', function() {
    $('#add-filters').find('i').removeClass('fa-chevron-down').addClass('fa-chevron-up');
})

$('#collapseFilter').on('hidden.bs.collapse', function() {
    $('#add-filters').find('i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
})

function formatTaxa (taxa) {
    if (taxa.loading) {
        return taxa.text;
    }
    var $container = $(
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

$(document).ready(function () {
    const fullUrl = new URL(window.location.href);
    const urlParams = fullUrl.searchParams;
    let totalAllFilters = 0;
    let url = ''
    let taxonName = ''

    if (!urlParams.get('selected')) {
        selectedTaxonGroup = $($('#sortable').children()[0]).data('id');
        if (selectedTaxonGroup) {
            urlParams.set('selected', selectedTaxonGroup);
            history.pushState({}, null, fullUrl.href);
        }
    } else {
        selectedTaxonGroup = urlParams.get('selected');
    }

    if (selectedTaxonGroup) {
        $('#sortable').find(`[data-id="${selectedTaxonGroup}"]`).addClass('selected');
        url = `/api/taxa-list/?taxonGroup=${selectedTaxonGroup}`
    }

    $('#taxa-auto-complete').select2({
        ajax: {
            url: '/species-autocomplete/',
            dataType: 'json',
            data: function (params) {
                let query = {
                    term: params.term,
                    taxonGroupId: urlParams.get('selected')
                }
                return query;
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
        url += `&validated=${urlParams.get('validated')}`;
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
            let option = new Option(`${result['canonical_name']} (${result['rank']})`, result.id, true, true);
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
    if (url) {
        getTaxaList(url);
    }
    $('.select-multiple').select2();
});


hideLoading();
