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

    function formatLoadingMessage() {
        return `<div style="padding-left:50px;">Loading...</div>`;
    }

    const getTaxaList = (url) => {
        taxaUrlList = url;
        loading.show();
        let urlParams = new URLSearchParams(window.location.search);
        let initialPage = urlParams.get('page') ? parseInt(urlParams.get('page')) : 1;
        let initialPageSize = urlParams.get('page_size') ? parseInt(urlParams.get('page_size')) : 25;
        let initialSortOrder = urlParams.get('o') ? urlParams.get('o').replace('-', '') : 'canonical_name';
        let initialSortBy = urlParams.get('o') ? (urlParams.get('o').includes('-') ? '-' : '') : '';
        let initialStart = (initialPage - 1) * 20;

        $('.download-button-container').show();
        let table = $('#taxaTable').DataTable({
            "processing": true,
            "serverSide": true,
            "ordering": true,
            "order": [],
            "scrollX": true,
            "fixedColumns": {
                "start": 0,
                "end": 1
            },
            scrollY: 'calc(100vh - 325px)',
            "scrollCollapse": true,
            "initComplete": function(settings, json) {
                let columnIdx = settings.aoColumns.findIndex(col => col.data === (initialSortOrder ? initialSortOrder : 'canonical_name'));
                let initialOrder = [columnIdx, initialSortBy.includes('-') ? 'desc' : 'asc'];
                this.api().order(initialOrder).draw(false);
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
                        window.location.href = `/taxonomy/edit/${selectedTaxonGroup}/${data.id}/?next=${location.href}`;
                    }
                });

                $('.add-tag').off('click').on('click', function (event) {
                    event.preventDefault();
                    if (!taxaData) return false;
                    let data = taxaData.find(taxon => taxon.id === $(this).parent().data('id'));
                    $('#addTagModal').modal({keyboard: false});
                    $('#addTagModal').find('.save-tag').data('taxonomy-id', data.id);
                    let tagsString = data.tag_list;
                    let tagsArray = tagsString.split(',').filter(n => n);
                    let formattedTags = tagsArray.map(tag => ({id: tag, text: tag, name: tag}));
                    const tagAutoComplete = $('#taxa-tag-auto-complete');
                    tagAutoComplete.empty().val(null).trigger('change');
                    if (tagsArray.length > 0) {
                        const tagIds = [];
                        tagsArray.forEach(tag => {
                            let newOption = new Option(tag, tag, false, false);
                            tagAutoComplete.append(newOption);
                            tagIds.push(tag);
                        });
                        tagAutoComplete.val(tagIds).trigger('change');
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
                            let searchUrl = `/map/#search/${name}/taxon=&search=${name}&sourceCollection=${JSON.stringify(sourceCollection)}`;
                            let taxonomicStatusHTML = (data.taxonomic_status && data.taxonomic_status.toLowerCase() === 'synonym') ?
                                ` <span class="badge badge-info">Synonym</span>` : '';
                            let gbifHTML = data.gbif_key ? ` <a href="https://www.gbif.org/species/${data.gbif_key}" target="_blank"><span class="badge badge-warning">GBIF</span></a>` : '';
                            let iucnHTML = data.iucn_redlist_id ? ` <a href="https://apiv3.iucnredlist.org/api/v3/taxonredirect/${data.iucn_redlist_id}/" target="_blank"><span class="badge badge-danger">IUCN</span></a>` : '';
                            let validatedHTML = !data.validated ? '<span class="badge badge-secondary">Unvalidated</span>' : '';

                            data.nameHTML = name + taxonomicStatusHTML + '<br/>' + gbifHTML + iucnHTML + validatedHTML;

                            if (userCanEditTaxon || isExpert) {
                                let $rowAction = $('.row-action').clone(true, true).removeClass('row-action');
                                if (!data['validated']) {
                                    $rowAction.find('.btn-validated-container').hide();
                                    if (data['can_be_validated']) {
                                        $rowAction.find('.btn-unvalidated-container').show();
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
                    "className": "min-width-100"
                },
                {"data": "family", "className": "min-width-100"},
                {"data": "genus", "className": "min-width-100"},
                {"data": "species", "className": "min-width-100"},
                {"data": "author", "className": "min-width-100"},
                {"data": "biographic_distribution", "className": "min-width-100", "sortable": false},
                {"data": "rank", "className": "min-width-100"},
                {"data": "iucn_status_full_name", "orderData": [8], "orderField": "iucn_status__category"},
                // {"data": "origin_name"},
                // {"data": "endemism_name", "orderData": [4], "orderField": "endemism__name"},
                // {
                //     "data": "total_records",
                //     "render": function (data, type, row) {
                //         let searchUrl = `/map/#search/${row.canonical_name}/taxon=&search=${row.canonical_name}&sourceCollection=${JSON.stringify(sourceCollection)}`;
                //         return `${data} <a href='${searchUrl}' target="_blank"><i class="fa fa-search" aria-hidden="true"></i></a>`;
                //     }
                // },
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

        // Event listener for detail rows
        table.on('click', 'tbody td.dt-control', async function (event) {
            let tr = event.target.closest('tr');
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
