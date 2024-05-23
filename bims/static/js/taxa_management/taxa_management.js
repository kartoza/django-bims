import { taxaSidebar } from './taxa_sidebar.js';
import { taxaTable } from "./taxa_table.js";
import { addNewTaxon} from "./add_new_taxon.js";


export const taxaManagement = (() => {
    const fullUrl = new URL(window.location.href);
    const urlParams = fullUrl.searchParams;
    const $loadingOverlay = $('.loading');
    const $saveTaxonBtn = $('#saveTaxon');

    let taxaUrlList = '';
    let $sortable = $('#sortable');

    const loading = {
        hide: () => {
            $loadingOverlay.hide();
        },
        show: () => {
            $loadingOverlay.show();
        }
    }

    let selectedTaxonGroup = '';

    function init() {
        if (!urlParams.get('selected')) {
            selectedTaxonGroup = $($('#sortable').children()[0]).data('id');
            if (selectedTaxonGroup) {
                urlParams.set('selected', selectedTaxonGroup);
                history.pushState({}, null, fullUrl.href);
            }
        } else {
            selectedTaxonGroup = urlParams.get('selected');
        }

        if (typeof selectedTaxonGroup === 'undefined') {
            loading.hide();
        }

        taxaSidebar.init(selectedTaxonGroup)
        taxaTable.init(getTaxaList, selectedTaxonGroup)
        addNewTaxon.init(selectedTaxonGroup)

        $saveTaxonBtn.on('click', handleSubmitEditTaxon)

        if (userCanEditTaxonGroup) {
            $sortable.sortable({
                stop: function (event, ui) {
                    let $li = $(event.target).find('li');
                    let ids = [];
                    $.each($li, function (index, element) {
                        ids.push($(element).data('id'));
                    });
                    $sortable.sortable("disable");
                    loading.show();
                    $.ajax({
                        url: '/api/update-taxon-group-order/',
                        headers: {"X-CSRFToken": csrfToken},
                        type: 'POST',
                        data: {
                            'taxonGroups': JSON.stringify(ids)
                        },
                        success: function (response) {
                            loading.hide();
                            $sortable.sortable("enable");
                        }
                    });
                }
            });
        }

        $('#download-csv').on('click', handleDownloadCsv)
    }

    function handleSubmitEditTaxon(event) {
        event.preventDefault();
        $saveTaxonBtn.html('Processing...')
        $saveTaxonBtn.attr('disabled', true)
        const $form = $('#editTaxonForm');
        let formData = $form.serialize();
        $.ajax({
            url: $form.attr('action'),
            type: 'PUT',
            data: formData,
            headers: {"X-CSRFToken": csrfToken},
            success: function(response) {
                console.log('Success:', response);
                location.reload();
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                alert('Failed to update taxon: ' + error);
            },
            complete: function() {
                $saveTaxonBtn.html('Save Changes');
                $saveTaxonBtn.removeAttr('disabled');
            }
        });
    }

    function handleDownloadCsv(e) {

        const $target = $(e.target);
        const targetHtml = $target.html();
        const targetWidth = $target.width();
        showDownloadPopup('REPORT', 'Taxa List', function () {
            $target.prop('disabled', true);
            $target.html(`<div style="width: ${targetWidth}px;"><img src="/static/images/default/grid/loading.gif" width="20"/></div>`);
            fetch(taxaUrlList.replace('/api/taxa-list/', '/download-csv-taxa-list/'))
                .then((resp) => {
                    $target.prop('disabled', false);
                    $target.html(targetHtml);
                    alert(downloadRequestMessage);
                })
                .catch(() => alert('Cannot download the file'));
        })
    }

    const onEditTaxonFormChanged = (elm, event='change') => {
        elm.on(event, function (e) {
            $saveTaxonBtn.attr('disabled', false);
        })
    }

    const getValuesAfterArrow = (obj) => {
        let results = {};

        // Helper function to check each value
        function checkValue(key, value) {
            if (typeof value === 'string') {
                const parts = value.split('→');
                if (parts.length > 1) {
                    results[key] = parts[1].trim();
                } else {
                    results[key] = value
                }
            } else {
                results[key] = value;
            }
        }

        // Loop through each key-value pair in the object
        for (const key in obj) {
            checkValue(key, obj[key]);
        }

        return results;
    }


    const editTaxonClicked = (data) => {
        const template = _.template($('#editTaxonForm').html());
        data['taxon_group_id'] = selectedTaxonGroup;
        const taxonData = getValuesAfterArrow(data);
        const form = template(taxonData);
        const modal = $('#editTaxonModal');

        modal.find('.modal-body').html(form);

        modal.find('#rank-options').val(taxonData['rank'])
        modal.find('#cons-status-options').val(taxonData['iucn_status_name'])
        modal.find('#origin-options').val(taxonData['origin'])
        modal.find('#endemism-options').val(taxonData['endemism_name'])

        onEditTaxonFormChanged(modal.find('#rank-options'));
        onEditTaxonFormChanged(modal.find('#cons-status-options'));
        onEditTaxonFormChanged(modal.find('#origin-options'));
        onEditTaxonFormChanged(modal.find('#endemism-options'));
        onEditTaxonFormChanged(modal.find('#scientific_name'), 'input');
        onEditTaxonFormChanged(modal.find('#canonical_name'), 'input');

        $saveTaxonBtn.attr('disabled', true);
        modal.modal('show');
    }

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
    const getTaxaList = (url) => {
        taxaUrlList = url;
        loading.show();
        $('.download-button-container').show();
        $.get(url).then(
            function (response) {
                loading.hide();
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
                    let name = data.canonical_name || data.scientific_name;
                    let searchUrl = `/map/#search/${name}/taxon=&search=${name}&sourceCollection=${JSON.stringify(sourceCollection)}`;
                    let scientificNameHTML = `<br/><span style="font-size: 9pt">${data.scientific_name}</span><br/>`;
                    let commonNameHTML = data.common_name ? ` <span class="badge badge-info">${data.common_name}</span><br/>` : '';
                    let taxonomicStatusHTML = (data.taxonomic_status && data.taxonomic_status.toLowerCase() === 'synonym') ?
                                              ` <span class="badge badge-info">Synonym</span>` : '';
                    let dividerHTML = (data.gbif_key || data.iucn_redlist_id) ?
                                      '<div style="border-top: 1px solid black; margin-top: 5px; margin-bottom: 5px;"></div>' : '';
                    let gbifHTML = data.gbif_key ?
                                   ` <a href="https://www.gbif.org/species/${data.gbif_key}" target="_blank"><span class="badge badge-warning">GBIF</span></a>` : '';
                    let iucnHTML = data.iucn_redlist_id ?
                                   ` <a href="https://apiv3.iucnredlist.org/api/v3/taxonredirect/${data.iucn_redlist_id}/" target="_blank"><span class="badge badge-danger">IUCN</span></a>` : '';
                    let validatedHTML = !data.validated ? '<span class="badge badge-secondary">Unvalidated</span>' : '';

                    name += scientificNameHTML + commonNameHTML + taxonomicStatusHTML + dividerHTML + gbifHTML + iucnHTML + validatedHTML;

                    let $rowAction = $('.row-action').clone(true, true).removeClass('row-action');

                    if ((userCanEditTaxon || isExpert)) {
                        $rowAction.removeClass('row-action');
                        if (!data['validated']) {
                            $rowAction.find('.btn-validated-container').hide();
                            if (data['can_be_validated']) {
                                $rowAction.find('.btn-unvalidated-container').show();
                            }
                        } else {
                            $rowAction.find('.btn-validated-container').show();
                            $rowAction.find('.btn-unvalidated-container').hide();
                        }
                        $rowAction.show();
                        setTimeout(function () {
                            $('[data-toggle="tooltip"]').tooltip();
                            $('[data-toggle="popover"]').popover();
                        }, 100)
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
                    $row.append(
                        `<td style="width: 120px;">${data['tag_list'].split(',').map(function (tag) {
                            return `<span class="badge badge-info">${tag}</span>`
                        }).join('')}</td>`
                    );

                    if (userCanEditTaxon || isExpert) {
                        let $tdAction = $(`<td style="width: 85px;"></td>`);
                        $row.append($tdAction);
                        $tdAction.append($rowAction);
                        $rowAction.find('.edit-taxon').click((event) => {
                            event.preventDefault();
                            editTaxonClicked(data);
                            return false;
                        });
                        $rowAction.find('.add-tag').click((event) => {
                            $('#addTagModal').modal({
                                keyboard: false
                            });
                            $('#addTagModal').find('.save-tag').data('taxonomy-id', data['id']);
                            let tagsString = data['tag_list'];
                            let tagsArray = tagsString.split(',').filter(n => n);
                            let formattedTags = tagsArray.map(function(tag) {
                                return { id: tag, text: tag, name: tag};
                            });
                            const tagAutoComplete = $('#taxa-tag-auto-complete');
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
                            insertParam('page', urlParams.get('page') ? urlParams.get('page') : 1, false);
                        })
                    } else {
                        paginationPrev.hide();
                    }
                }
            }
        )

        $("#add-taxon-input").on("keydown", function(event) {
            if(event.which === 13) {
                $('#find-taxon-button').click();
            }
        });
    }

    return {
        init,
    }
})();

document.addEventListener('DOMContentLoaded', taxaManagement.init);
