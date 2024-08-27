import { taxaSidebar } from './taxa_sidebar.js';
import { taxaTable } from "./taxa_table.js";
import { addNewTaxon} from "./add_new_taxon.js";
import { taxonDetail } from "./taxon_detail.js";

let taxaData = [];
let orderField = {
    'iucn_status_full_name': 'iucn_status__category',
    'endemism_name': 'endemism__name'
}


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

    function getTaxonGroupValidatedCount() {
        const allTaxaGroups = taxaSidebar.allTaxaGroups(JSON.parse(JSON.stringify(taxaGroups)));
        for (let taxaGroup of allTaxaGroups) {
            $.ajax({
                url: '/api/taxon-group-validated/' + taxaGroup.id + '/',
                headers: {"X-CSRFToken": csrfToken},
                type: 'GET',
                success: function (response) {
                    $('#taxon_group_validated_' + taxaGroup.id).text(response.total_validated);
                    if (response.total_unvalidated > 0) {
                        $('#taxon_group_validated_' + taxaGroup.id).parent().after($('<div class="taxon-group-badge">\n' +
                            `<span id="taxon_group_unvalidated_${taxaGroup.id}">${response.total_unvalidated}</span> Unvalidated\n` +
                            '</div>'))
                    }
                }
            });
        }
    }

    function init() {
        loading.hide();
        if (!urlParams.get('selected')) {
            selectedTaxonGroup = $($('#sortable').children()[0]).data('id');
            if (selectedTaxonGroup) {
                urlParams.set('selected', selectedTaxonGroup);
                history.pushState({}, null, fullUrl.href);
            }
        } else {
            selectedTaxonGroup = urlParams.get('selected');
        }

        taxaSidebar.init(updateTaxonGroup, selectedTaxonGroup)
        taxaTable.init(getTaxaList, selectedTaxonGroup)
        addNewTaxon.init(selectedTaxonGroup)

        getTaxonGroupValidatedCount();

        $saveTaxonBtn.on('click', handleSubmitEditTaxon)
        $('#download-csv').on('click', handleDownloadCsv)

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
        showDownloadPopup('REPORT', 'Taxa List', function (downloadRequestId) {
            $target.prop('disabled', true);
            $target.html(`<div style="width: ${targetWidth}px;"><img src="/static/images/default/grid/loading.gif" width="20"/></div>`);
            let downloadUrl = taxaUrlList.replace('/api/taxa-list/', '/download-csv-taxa-list/')
            if (!downloadUrl.includes('?')) {
                downloadUrl += '?';
            }
            downloadUrl += '&downloadRequestId=' + downloadRequestId
            fetch(downloadUrl)
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

    function formatLoadingMessage() {
        return `<div style="padding-left:50px;">Loading...</div>`;
    }

    function getColumnMapping(dataTable) {
        let columns = dataTable.settings().init().columns;
        let columnMapping = {};
        columns.forEach((column, index) => {
            columnMapping[column.data] = index;
        });
        return columnMapping;
    }

    function updateSortIcon(columnIndex, sortDirection) {
        let headerCell = $('#taxaTable_wrapper thead th').eq(columnIndex);
        headerCell.removeClass('dt-ordering-asc dt-ordering-desc');
        if (sortDirection === 'asc') {
            headerCell.addClass('dt-ordering-asc');
        } else if (sortDirection === 'desc') {
            headerCell.addClass('dt-ordering-desc');
        }
    }

    function replaceTaxonGroup(url, newTaxonGroup) {
        return url.replace(/(taxonGroup=)\d+/, `$1${newTaxonGroup}`);
    }

    function updateTaxonGroup(taxonGroupId) {
        selectedTaxonGroup = taxonGroupId;
        let table = $('#taxaTable').DataTable();
        table.destroy();
        let newParams = new URLSearchParams(window.location.search);
        newParams.set('selected', taxonGroupId);

        if (newParams) {
            let urlParams = new URLSearchParams(newParams);
            let currentUrl = new URL(window.location);
            for (let param of urlParams.entries()) {
                currentUrl.searchParams.set(param[0], param[1]);
            }
            window.history.pushState({}, '', currentUrl);
        }

        let taxaUrlParams = new URLSearchParams(taxaUrlList)
        if (taxaUrlParams.get('taxonGroup') !== newParams.get('selected')) {
            taxaUrlList = replaceTaxonGroup(taxaUrlList, newParams.get('selected'))
        }
        getTaxaList(taxaUrlList, newParams);
    }

    const getTaxaList = (url) => {
        taxaUrlList = url;
        let urlParams = new URLSearchParams(window.location.search);
        let initialPage = urlParams.get('page') ? parseInt(urlParams.get('page')) : 1;
        let initialPageSize = urlParams.get('page_size') ? parseInt(urlParams.get('page_size')) : 25;
        let initialSortOrder = urlParams.get('o') ? urlParams.get('o').replace('-', '') : 'canonical_name';
        let initialSortBy = urlParams.get('o') ? (urlParams.get('o').includes('-') ? '-' : '') : '';
        let initialStart = (initialPage - 1) * 20;

        $('.download-button-container').show();
        let tableInitialized = false;

        let table = $('#taxaTable').DataTable({
            "processing": true,
            "serverSide": true,
            "ordering": true,
            "order": [],
            "scrollX": true,
            "autoWidth": false,
            "fixedColumns": {
                "start": 0,
                "end": 1
            },
            scrollY: 'calc(100vh - 325px)',
            "scrollCollapse": true,
            "initComplete": function(settings, json) {
                if (!tableInitialized) {
                    let columnIdx = settings.aoColumns.findIndex(col => col.data === (initialSortOrder ? initialSortOrder : 'canonical_name'));
                    let initialOrder = [columnIdx, initialSortBy.includes('-') ? 'desc' : 'asc'];
                    this.api().order(initialOrder);
                    let columnMapping = getColumnMapping(table);
                    let columnIndex = columnMapping[initialSortOrder];
                    updateSortIcon(columnIndex, initialSortBy.includes('-') ? 'desc' : 'asc');
                    tableInitialized = true;
                }
            },
            "drawCallback": function (settings) {
                $(".dropdown-action").each(function () {
                    let parent, dropdownMenu, left, top;
                    $(this).off('show.bs.dropdown hidden.bs.dropdown'); // Prevent multiple bindings
                    $(this).on('show.bs.dropdown', function () {
                        parent = $(this).parent();
                        dropdownMenu = $(this).find('.dropdown-menu');
                        left = dropdownMenu.offset().left - $(window).scrollLeft();
                        top = dropdownMenu.offset().top - $(window).scrollLeft();
                        $('body').append(dropdownMenu.css({position: 'fixed', left: left, top: top}).detach());
                    });
                    $(this).on('hidden.bs.dropdown', function () {
                        $(this).append(dropdownMenu.css({position: 'absolute', left: false, top: false}).detach());
                    });
                });

                $('.edit-taxon').off('click').on('click', function(event) {
                    event.preventDefault();
                    if (!taxaData) return false;
                    let data = taxaData.find(taxon => taxon.id === $(this).parent().data('id'));
                    if (data) {
                        window.location.href = `/taxonomy/edit/${selectedTaxonGroup}/${data.id}/?next=${encodeURIComponent(location.href)}`;
                    }
                });

                $('.edit-taxon-in-admin').off('click').on('click', function(event) {
                    event.preventDefault();
                    if (!taxaData) return false;

                    let data = taxaData.find(taxon => taxon.id === $(this).parent().data('id'));
                    if (data) {
                        let width = 800;
                        let height = 600;
                        let left = (screen.width / 2) - (width / 2);
                        let top = (screen.height / 2) - (height / 2);
                        let adminUrl = `/admin/bims/taxonomy/${data.id}/change/?_popup=1`;
                        let popup = window.open(adminUrl, 'EditTaxonAdmin', `width=${width},height=${height},top=${top},left=${left}`);

                        let popupInterval = setInterval(function() {
                            if (popup.closed) {
                                clearInterval(popupInterval);
                                if (window.wasFormSaved) {
                                    window.location.reload();
                                }
                            }
                        }, 500);
                    }
                });

                $('.remove-taxon-from-group').off('click').on('click', function (event) {
                    taxaTable.handleRemoveTaxonFromGroup($(this).parent().data('id'));
                });

                $('.reject-taxon').off('click').on('click', function (event) {
                    event.preventDefault();
                    taxaTable.handleRejectTaxon($(this).parent().data('id'));
                });

                $('.validate-taxon').off('click').on('click', function (event) {
                    event.preventDefault();
                    taxaTable.handleValidateTaxon($(this).parent().data('id'));
                });
            },
            "displayStart": initialStart,
            "ajax": function (data, callback, settings) {
                let page = urlParams.has('page') && settings.iDraw === 1 ? initialPage : Math.ceil(data.start / data.length) + 1;
                let pageSize = data.length;
                let sortBy = urlParams.get('o') && settings.iDraw == 1 ? initialSortOrder : (data.order.length ? data.columns[data.order[0].column].data : 'canonical_name');
                let sortOrder = urlParams.get('o') && settings.iDraw === 1 ? initialSortBy : (data.order.length && data.order[0].dir === 'desc' ? '-' : '');
                let order = sortOrder + sortBy;

                var currentUrl = new URL(window.location);
                currentUrl.searchParams.set('page', page);
                currentUrl.searchParams.set('page_size', pageSize);
                currentUrl.searchParams.set('o', order);
                window.history.pushState({}, '', currentUrl)

                let orderParam = sortOrder + (orderField.hasOwnProperty(sortBy) ? orderField[sortBy] : sortBy);

                $.ajax({
                    url: url,
                    data: {o: orderParam, page: page, page_size: pageSize},
                    success: function (response) {
                        loading.hide();
                        taxaData = response.results;
                        $.each(response.results, function (index, data) {
                            let name = data.canonical_name || data.scientific_name;
                            let taxonomicStatusHTML = (data.taxonomic_status && data.taxonomic_status.toLowerCase() === 'synonym') ?
                                ` <span class="badge badge-info">Synonym</span>` : '';
                            let gbifHTML = data.gbif_key ? ` <a href="https://www.gbif.org/species/${data.gbif_key}" target="_blank"><span class="badge badge-warning">GBIF</span></a>` : '';
                            let iucnHTML = data.iucn_redlist_id ? ` <a href="https://apiv3.iucnredlist.org/api/v3/taxonredirect/${data.iucn_redlist_id}/" target="_blank"><span class="badge badge-danger">IUCN</span></a>` : '';
                            let validatedHTML = !data.validated ? '<span class="badge badge-secondary">Unvalidated</span>' : '';

                            data.nameHTML = name + '<br/>' + gbifHTML + iucnHTML + validatedHTML + `<input type="hidden" class="proposal-id" value="${data.proposal_id}" />`;

                            if (data['can_edit']) {
                                let $rowAction = $('.row-action').clone(true, true).removeClass('row-action');
                                if (!data['validated']) {
                                    $rowAction.find('.btn-validated-container').hide();
                                    if (data['can_be_validated']) {
                                        $rowAction.find('.btn-unvalidated-container').show();
                                    } else {
                                        $rowAction.find('.btn-unvalidated-container').hide();
                                    }
                                } else {
                                    $rowAction.find('.btn-validated-container').show();
                                    $rowAction.find('.btn-unvalidated-container').hide();
                                }
                                $rowAction.find('.dropdown-menu').attr('data-id', data['id']);
                                $rowAction.show();
                                data.rowActionHTML = $rowAction.html();
                            } else {
                                data.rowActionHTML = '';
                            }
                        });
                        callback({
                            draw: data.draw,
                            recordsTotal: response.count,
                            recordsFiltered: response.count,
                            data: response.results
                        });
                    }
                });
            },
            "columns": [
                 {
                    class: 'dt-control',
                    orderable: false,
                    data: null,
                    defaultContent: '',
                },
                {
                    "data": "canonical_name",
                    "render": function (data, type, row) {
                        return row.nameHTML;
                    },
                    "className": "min-width-150"
                },
                {"data": "family", "className": "min-width-100"},
                {"data": "genus", "className": "min-width-100"},
                {"data": "species", "className": "min-width-100"},
                {"data": "taxonomic_status", "className": "min-width-100"},
                {"data": "author", "className": "min-width-100"},
                {"data": "biographic_distributions", "className": "min-width-100", "sortable": false,
                    "render": function (data) {
                        return data.split(',').map(tag => `<span class="badge badge-info">${tag}</span>`).join('');
                    }
                },
                {"data": "common_name", "className": "min-width-100", "sortable": false},
                {"data": "rank", "className": "min-width-100"},
                {"data": "iucn_status_full_name", "orderData": [8], "orderField": "iucn_status__category"},
                {"data": "import_date", "className": "min-width-100"},
                {
                    "data": "tag_list",
                    "sortable": false,
                    "className": "min-width-100",
                    "searchable": false,
                    "render": function (data) {
                        return data.split(',').map(tag => `<span class="badge badge-info">${tag}</span>`).join('');
                    }
                },
                {
                    "data": "rowActionHTML",
                    "sortable": false,
                    "searchable": false
                }
            ],
            "pageLength": initialPageSize,
            "pagingType": "simple_numbers",
            "searching": false
        });

        const detailRows = [];
        const taxonCache = {};
        const taxonProposalCache = {};

        // Event listener for detail rows
        table.on('click', 'tbody td.dt-control', async function (event) {
            let tr = event.target.closest('tr');
            let proposalId = $(this).closest('tr').find('.proposal-id').val();

            let row = table.row(tr);
            let idx = detailRows.indexOf(tr.id);

            if (row.child.isShown()) {
                tr.classList.remove('details');
                row.child.hide();
                detailRows.splice(idx, 1);
            } else {
                tr.classList.add('details');

                if (!taxonCache[tr.id]) {
                    row.child(formatLoadingMessage()).show();
                    try {
                        let response = await fetch(`/api/taxon/${tr.id.replace('row_', '')}`);
                        let data = await response.json();
                        taxonCache[tr.id] = data;
                        row.child(taxonDetail.formatDetailTaxon(data)).show();
                    } catch (error) {
                        console.error('Error fetching taxon data:', error);
                        row.child('<div style="padding-left:50px; color: red;">Failed to load data</div>').show();
                        return;
                    }
                } else {
                    row.child(taxonDetail.formatDetailTaxon(taxonCache[tr.id])).show();
                }

                if (proposalId && proposalId !== 'null') {
                    try {
                        let response = await fetch(`/api/taxon-proposal/${proposalId}`);
                        let data = await response.json();
                        let $tr = $(row.child())
                        let $changes = $('<div class="taxon_proposal"><div>Updates</div></div>')
                        $changes.append(taxonDetail.formatDetailTaxon(data))
                        $tr.find('td').append($changes);
                    } catch (error) {
                        console.error('Error fetching taxon data:', error);
                        return;
                    }
                }

                if (idx === -1) {
                    detailRows.push(tr.id);
                }
            }
        });

        // Redraw event to open details for stored rows
        table.on('draw', () => {
            detailRows.forEach((id) => {
                let el = document.querySelector('#' + id + ' td.dt-control');
                if (el) {
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }
            });
        });

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
