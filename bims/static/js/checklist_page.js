(function ($) {
    const $page = $('#checklist-page');

    if (!$page.length) {
        return;
    }

    const csrfToken = $page.data('csrf-token');
    const canPublish = $page.data('can-publish') === true || $page.data('can-publish') === 'true';
    const isSuperuser = $page.data('is-superuser') === true || $page.data('is-superuser') === 'true';
    const publishGroupIds = String($page.data('publish-group-ids') || '')
        .split(',')
        .map(function (value) {
            return parseInt(value, 10);
        })
        .filter(function (value) {
            return !Number.isNaN(value);
        });
    const apiBase = $page.data('api-base');

    let nextUrl = null;
    let prevUrl = null;
    let currentPage = 1;

    const $groupSelect = $('#group-select');
    const $statusSelect = $('#status-select');
    const $loading = $('#version-loading');
    const $table = $('#version-table');
    const $tbody = $('#version-tbody');
    const $empty = $('#version-empty');
    const $paginator = $('#paginator-wrapper');
    const $btnPrev = $('#btn-prev');
    const $btnNext = $('#btn-next');
    const $pageInfo = $('#page-info');
    const $pgPrev = $('#pg-prev');
    const $pgNext = $('#pg-next');

    function canPublishGroup(groupId) {
        if (isSuperuser) {
            return true;
        }
        return publishGroupIds.indexOf(parseInt(groupId, 10)) !== -1;
    }

    function updateTableStateAfterRowRemoval() {
        if ($tbody.children('tr').length === 0) {
            $table.hide();
            $empty.show();
            $paginator.hide();
        }
    }

    function getParam(key) {
        return new URLSearchParams(window.location.search).get(key);
    }

    function pushParams(groupId, status) {
        const url = new URL(window.location.href);
        url.searchParams.set('module', groupId);
        if (status) {
            url.searchParams.set('status', status);
        } else {
            url.searchParams.delete('status');
        }
        window.history.pushState({ module: groupId, status: status }, '', url.toString());
    }

    function statusBadge(status, isPublishing) {
        const display = (status === 'draft' && isPublishing) ? 'publishing' : status;
        return '<span class="badge badge-pill badge-' + display + '">' +
            display.charAt(0).toUpperCase() + display.slice(1) +
            '</span>';
    }

    function changesBadge(v) {
        if (v.status !== 'published') {
            return '<span class="text-muted">—</span>';
        }
        const parts = [];
        if (v.additions_count)  parts.push('<span class="text-success font-weight-bold">+' + v.additions_count + '</span>');
        if (v.deletions_count)  parts.push('<span class="text-danger font-weight-bold">-' + v.deletions_count + '</span>');
        if (v.updates_count)    parts.push('<span class="text-primary">~' + v.updates_count + '</span>');
        return parts.length ? parts.join(' ') : '<span class="text-muted">—</span>';
    }

    function fmtDate(iso) {
        return iso
            ? new Date(iso).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            })
            : '—';
    }

    function renderRows(versions) {
        return versions.map(function (v) {
            return `
                <tr>
                    <td>
                        <a href="#" class="font-weight-bold version-detail-link"
                           data-id="${v.id}">${v.version}</a>
                    </td>
                    <td>${statusBadge(v.status, v.is_publishing)}</td>
                    <td>${v.status === 'published'
                        ? v.taxa_count
                        : '<span class="text-muted" title="Taxa snapshot is only available after publishing">—</span>'}</td>
                    <td class="text-nowrap">${changesBadge(v)}</td>
                    <td>${v.doi
                        ? `<a href="${v.doi}" target="_blank" rel="noopener">${v.doi.length > 35 ? v.doi.substring(0, 35) + '…' : v.doi}</a>`
                        : '—'}</td>
                    <td>${fmtDate(v.published_at)}</td>
                    <td>${v.created_by_name || '—'}</td>
                    <td class="text-nowrap">
                        ${v.status === 'published' ? `
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-secondary dropdown-toggle"
                                        data-toggle="dropdown" title="Download">
                                    <i class="fa fa-download"></i>
                                </button>
                                <div class="dropdown-menu dropdown-menu-right">
                                    <a class="dropdown-item export-coldp-btn" href="#"
                                       data-id="${v.id}">ColDP ZIP</a>
                                    <a class="dropdown-item checklist-dl-csv" href="#"
                                       data-id="${v.id}">CSV Taxa List</a>
                                    <a class="dropdown-item checklist-dl-csv-family" href="#"
                                       data-id="${v.id}">CSV Taxa List by Family</a>
                                    <a class="dropdown-item checklist-dl-pdf" href="#"
                                       data-id="${v.id}">PDF</a>
                                </div>
                            </div>
                            ${canPublishGroup(v.taxon_group) ? `
                            <button class="btn btn-sm btn-outline-secondary edit-version-btn ml-1"
                                    data-id="${v.id}" data-version="${v.version}"
                                    data-doi="${escHtml(v.doi || '')}"
                                    data-notes="${escHtml(v.notes || '')}"
                                    title="Edit Notes &amp; DOI">
                                <i class="fa fa-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger remove-version-btn ml-1"
                                    data-id="${v.id}" data-version="${v.version}"
                                    title="Remove published version">
                                <i class="fa fa-trash"></i>
                            </button>` : ''}
                        ` : ''}
                        ${v.status === 'draft' && canPublishGroup(v.taxon_group)
                            ? (v.is_publishing
                                ? `<span class="text-muted">
                                       <span class="spinner-border spinner-border-sm" role="status"></span>
                                       Processing…
                                   </span>`
                                : `<button class="btn btn-sm btn-outline-primary publish-version-btn"
                                           data-id="${v.id}" data-version="${v.version}"
                                           title="Publish this version">
                                       <i class="fa fa-check"></i> Publish
                                   </button>
                                   <button class="btn btn-sm btn-outline-danger delete-draft-btn ml-1"
                                           data-id="${v.id}" data-version="${v.version}"
                                           title="Delete draft">
                                       <i class="fa fa-trash"></i>
                                   </button>`)
                            : ''}
                    </td>
                </tr>`;
        }).join('');
    }

    async function loadVersions(url) {
        $loading.show();
        $table.hide();
        $empty.hide();
        $paginator.hide();

        try {
            const resp = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
            const data = await resp.json();

            nextUrl = data.next;
            prevUrl = data.previous;

            const results = data.results || [];
            if (results.length) {
                $tbody.html(renderRows(results));
                $table.show();
            } else {
                $empty.show();
            }

            if (data.count > results.length || prevUrl) {
                $pageInfo.text(`Page ${currentPage} of ${Math.ceil(data.count / 20)}`);
                $pgPrev.toggleClass('disabled', !prevUrl);
                $pgNext.toggleClass('disabled', !nextUrl);
                $paginator.show();
            }
        } catch (e) {
            $tbody.html(`<tr><td colspan="8" class="text-danger">Failed to load: ${e.message}</td></tr>`);
            $table.show();
        } finally {
            $loading.hide();
        }
    }

    function buildUrl(groupId, status, page) {
        let url = `${apiBase}?taxon_group=${groupId}&page=${page || 1}`;
        if (status) {
            url += `&status=${status}`;
        }
        return url;
    }

    function reload() {
        currentPage = 1;
        const groupId = $groupSelect.val();
        const status = $statusSelect.length ? $statusSelect.val() : '';
        pushParams(groupId, status);
        loadVersions(buildUrl(groupId, status, 1));
        $('#av-group').val(groupId);
    }

    const initGroup = getParam('module') || $groupSelect.find('option:first').val();
    const initStatus = getParam('status') || '';
    $groupSelect.val(initGroup);
    if ($statusSelect.length) {
        $statusSelect.val(initStatus);
    }
    loadVersions(buildUrl(initGroup, initStatus, 1));

    $groupSelect.on('change', reload);
    if ($statusSelect.length) {
        $statusSelect.on('change', reload);
    }

    $btnPrev.on('click', function (e) {
        e.preventDefault();
        if (prevUrl) {
            currentPage -= 1;
            loadVersions(prevUrl);
        }
    });

    $btnNext.on('click', function (e) {
        e.preventDefault();
        if (nextUrl) {
            currentPage += 1;
            loadVersions(nextUrl);
        }
    });

    window.addEventListener('popstate', function (e) {
        const state = e.state || {};
        if (state.module) {
            $groupSelect.val(state.module);
        }
        if ($statusSelect.length && state.status !== undefined) {
            $statusSelect.val(state.status);
        }
        loadVersions(buildUrl($groupSelect.val(), $statusSelect.length ? $statusSelect.val() : '', 1));
    });

    function showError(msg) {
        $('#add-version-error').text(msg).removeClass('d-none');
        $('#add-version-success').addClass('d-none');
    }

    function showSuccess(msg) {
        $('#add-version-success').text(msg).removeClass('d-none');
        $('#add-version-error').addClass('d-none');
    }

    async function loadPreviousVersions(groupId) {
        const $sel = $('#av-previous');
        $sel.empty().append('<option value="">Loading…</option>').prop('disabled', true);
        try {
            const resp = await fetch(
                `${apiBase}?taxon_group=${groupId}&status=published&page_size=100`,
                { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
            );
            const data = await resp.json();
            $sel.empty().append('<option value="">— None (first release) —</option>');
            (data.results || []).forEach(function (v) {
                const dateStr = v.published_at
                    ? new Date(v.published_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                    })
                    : 'unpublished';
                $sel.append($('<option>', {
                    value: v.id,
                    text: `${v.version} (${dateStr})`
                }));
            });
        } catch (e) {
            $sel.empty().append('<option value="">— None (first release) —</option>');
        } finally {
            $sel.prop('disabled', false);
        }
    }

    // -----------------------------------------------------------------------
    // Contributors state — live list edited inside the modal before saving
    // -----------------------------------------------------------------------
    let _contributors = [];   // [{user, first_name, last_name, email, organisation, note}]
    let _orgCounter  = 0;     // generates temporary IDs for org-only rows

    function renderContributors() {
        const $list = $('#av-contributors-list');
        if (!_contributors.length) {
            $list.html('<p class="text-muted small mb-0">No contributors. Add an organisation above.</p>');
            return;
        }
        const rows = _contributors.map(function (c, idx) {
            const nameCell = c.user
                ? `<span class="font-weight-bold">${escHtml(c.first_name)} ${escHtml(c.last_name)}</span>`
                : '<em class="text-muted">Organisation only</em>';
            const emailCell = c.user
                ? `<small class="text-muted">${escHtml(c.email)}</small>`
                : '';
            return `
                <div class="border rounded p-2 mb-2 contributor-row" data-idx="${idx}">
                  <div class="d-flex justify-content-between align-items-start">
                    <div style="flex:1">
                      <div>${nameCell} ${emailCell}</div>
                      <div class="mt-1 d-flex flex-wrap" style="gap:6px">
                        <input type="text"
                               class="form-control form-control-sm contributor-org"
                               placeholder="Organisation (optional)"
                               value="${escHtml(c.organisation)}"
                               style="max-width:220px">
                        <input type="text"
                               class="form-control form-control-sm contributor-note"
                               placeholder="Note / role (optional)"
                               value="${escHtml(c.note)}"
                               style="max-width:240px">
                      </div>
                    </div>
                    <button type="button"
                            class="btn btn-sm btn-outline-danger ml-2 remove-contributor-btn"
                            data-idx="${idx}" title="Remove">
                        &times;
                    </button>
                  </div>
                </div>`;
        });
        $list.html(rows.join(''));
    }

    function escHtml(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function syncContributorFields() {
        $('#av-contributors-list').find('.contributor-row').each(function () {
            const idx = parseInt($(this).data('idx'), 10);
            if (_contributors[idx] !== undefined) {
                _contributors[idx].organisation = $(this).find('.contributor-org').val().trim();
                _contributors[idx].note         = $(this).find('.contributor-note').val().trim();
            }
        });
    }

    async function loadGroupMembers(groupId) {
        const $loading = $('#av-contributors-loading');
        $loading.removeClass('d-none');
        _contributors = [];
        renderContributors();
        try {
            const resp = await fetch(
                `/api/checklist-version/group-members/?taxon_group=${groupId}`,
                { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
            );
            if (resp.ok) {
                _contributors = await resp.json();
            }
        } catch (e) { /* silent */ }
        finally { $loading.addClass('d-none'); }
        renderContributors();
    }

    $(document).on('click', '.remove-contributor-btn', function () {
        syncContributorFields();
        const idx = parseInt($(this).data('idx'), 10);
        _contributors.splice(idx, 1);
        renderContributors();
    });

    $('#btn-add-org-contributor').on('click', function () {
        syncContributorFields();
        _contributors.push({ user: null, first_name: '', last_name: '', email: '', organisation: '', note: '' });
        renderContributors();
        // Focus the last org input
        $('#av-contributors-list .contributor-org').last().focus();
    });

    if (canPublish) {
        $('#add-version-modal').on('show.bs.modal', function () {
            $('#add-version-error, #add-version-success').addClass('d-none').text('');
            $('#av-version, #av-doi, #av-notes').val('');
            const groupId = $groupSelect.val();
            $('#av-group').val(groupId);
            loadPreviousVersions(groupId);
            loadGroupMembers(groupId);
        });

        $('#av-group').on('change', function () {
            const groupId = $(this).val();
            loadPreviousVersions(groupId);
            loadGroupMembers(groupId);
        });

        function buildPayload() {
            const version = $('#av-version').val().trim();
            const licenceId = $('#av-licence').val();
            if (!version) {
                showError('Version string is required.');
                return null;
            }
            if (!licenceId) {
                showError('Licence is required.');
                return null;
            }
            const payload = {
                taxon_group: parseInt($('#av-group').val(), 10),
                version: version,
                license: parseInt(licenceId, 10)
            };
            const doi = $('#av-doi').val().trim();
            const notes = $('#av-notes').val().trim();
            const previous = ($('#av-previous').val() || '').trim();
            if (doi) {
                payload.doi = doi;
            }
            if (notes) {
                payload.notes = notes;
            }
            if (previous) {
                payload.previous_version = previous;
            }
            return payload;
        }

        async function syncContributorsAfterCreate(versionId) {
            syncContributorFields();
            const contribBase = `${apiBase}${versionId}/contributors/`;
            let serverContribs = [];
            try {
                const r = await fetch(contribBase, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                if (r.ok) {
                    serverContribs = await r.json();
                }
            } catch (e) { /* non-critical, skip */ }

            const desiredUserIds = new Set(
                _contributors.filter(function (c) { return c.user; }).map(function (c) { return c.user; })
            );

            const ops = [];
            serverContribs.forEach(function (sc) {
                if (sc.user && !desiredUserIds.has(sc.user)) {
                    ops.push(fetch(`${contribBase}${sc.id}/`, {
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': csrfToken }
                    }));
                } else if (sc.user) {
                    const desired = _contributors.find(function (c) { return c.user === sc.user; });
                    if (desired && (desired.organisation !== sc.organisation || desired.note !== sc.note)) {
                        ops.push(fetch(`${contribBase}${sc.id}/`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify({ organisation: desired.organisation, note: desired.note })
                        }));
                    }
                }
            });

            _contributors.filter(function (c) { return !c.user; }).forEach(function (c) {
                ops.push(fetch(contribBase, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ organisation: c.organisation, note: c.note })
                }));
            });

            await Promise.all(ops);
        }

        async function saveVersion(publish) {
            syncContributorFields();
            const payload = buildPayload();
            if (!payload) {
                return;
            }

            const $btn = publish ? $('#btn-save-publish') : $('#btn-save-draft');
            const origText = $btn.text();
            $btn.prop('disabled', true).text('Saving…');

            try {
                // 1. Create the draft
                const resp = await fetch(apiBase, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(function () { return {}; });
                    const nonField = (err.non_field_errors || []).join(' ');
                    if (nonField.includes('taxon_group') && nonField.includes('version')) {
                        showError('Version "' + payload.version + '" already exists for this module. Please use a different version string.');
                    } else {
                        showError(err.detail || nonField || JSON.stringify(err));
                    }
                    return;
                }
                const data = await resp.json();

                // 2. Sync contributor edits (remove/update/add) against the auto-created list
                await syncContributorsAfterCreate(data.id);

                if (!publish) {
                    showSuccess(`Draft "${data.version}" saved.`);
                    setTimeout(function () {
                        $('#add-version-modal').modal('hide');
                        reload();
                    }, 600);
                    return;
                }

                // 3. Kick off async publish — server sets is_publishing=True immediately
                //    and returns 202 before the snapshot work completes.
                const pubResp = await fetch(`${apiBase}${data.id}/publish/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken }
                });
                if (!pubResp.ok) {
                    const err = await pubResp.json().catch(function () { return {}; });
                    showError('Draft saved but publish failed: ' + (err.detail || JSON.stringify(err)));
                    return;
                }

                // 4. Close modal and reload — list now shows "Publishing" status
                $('#add-version-modal').modal('hide');
                reload();
                showPublishingBanner(data.id, data.version);

                // 5. Poll until is_publishing clears (Celery task finished)
                pollPublishing(data.id);

            } catch (e) {
                showError('Request failed: ' + e.message);
            } finally {
                $btn.prop('disabled', false).text(origText);
            }
        }

        let _publishingBanner = null;

        function showPublishingBanner(versionId, versionStr) {
            hidePublishingBanner();
            _publishingBanner = $(`
                <div id="publishing-banner" class="alert alert-info d-flex align-items-center mb-2" role="alert">
                    <span class="spinner-border spinner-border-sm mr-2" role="status"></span>
                    <span>Publishing <strong>${versionStr}</strong> — building taxa snapshot, this may take a moment…</span>
                </div>
            `);
            $('#version-table').before(_publishingBanner);
        }

        function hidePublishingBanner() {
            if (_publishingBanner) {
                _publishingBanner.remove();
                _publishingBanner = null;
            }
            $('#publishing-banner').remove();
        }

        function pollPublishing(versionId) {
            const interval = setInterval(async function () {
                try {
                    const r = await fetch(`${apiBase}${versionId}/`, {
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    });
                    if (!r.ok) { clearInterval(interval); hidePublishingBanner(); reload(); return; }
                    const v = await r.json();
                    if (!v.is_publishing) {
                        clearInterval(interval);
                        hidePublishingBanner();
                        reload();
                    }
                } catch (e) {
                    clearInterval(interval);
                    hidePublishingBanner();
                    reload();
                }
            }, 3000);
        }

        function showGlobalAlert(type, msg) {
            const $alert = $(`<div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${msg}
                <button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>
            </div>`);
            $('#version-table').before($alert);
            setTimeout(function () { $alert.alert('close'); }, 6000);
        }

        $('#btn-save-draft').on('click', function () {
            saveVersion(false);
        });

        $('#btn-save-publish').on('click', function () {
            if (!confirm('Publish this version now? This cannot be undone.')) {
                return;
            }
            saveVersion(true);
        });
    }

    function handleChecklistVersionDownload(e, output, orderBy) {
        e.preventDefault();
        const versionId = $(e.currentTarget).data('id');
        const title = output === 'pdf' ? 'PDF' : (orderBy === 'family' ? 'CSV Taxa List by Family' : 'CSV Taxa List');
        showDownloadPopup(output.toUpperCase(), title, function (downloadRequestId) {
            let url = '/download-checklist-snapshot/?checklistVersion=' + versionId +
                '&output=' + output +
                '&downloadRequestId=' + downloadRequestId;
            if (orderBy) {
                url += '&orderBy=' + orderBy;
            }
            fetch(url)
                .then(function () {
                    alert(downloadRequestMessage);
                })
                .catch(function () {
                    alert('Cannot download the file');
                });
        }, true, null, false);
    }

    $(document).on('click', '.checklist-dl-csv', function (e) {
        handleChecklistVersionDownload(e, 'csv', null);
    });

    $(document).on('click', '.checklist-dl-csv-family', function (e) {
        handleChecklistVersionDownload(e, 'csv', 'family');
    });

    $(document).on('click', '.checklist-dl-pdf', function (e) {
        handleChecklistVersionDownload(e, 'pdf', 'genus');
    });

    $(document).on('click', '.export-coldp-btn', function () {
        const versionId = $(this).data('id');
        showDownloadPopup(
            'ZIP',
            'Checklist ZIP',
            function (downloadRequestId) {
                $.ajax({
                    url: `${apiBase}${versionId}/export/`,
                    type: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    data: {
                        download_request_id: downloadRequestId
                    },
                    success: function () {
                        $('#alertModalBody').html(downloadRequestMessage);
                        $('#alertModal').modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    },
                    error: function (jqXHR, textStatus) {
                        let errorMessage = 'Failed to start checklist ZIP export.';
                        if (jqXHR.responseJSON && jqXHR.responseJSON.detail) {
                            errorMessage += ' ' + jqXHR.responseJSON.detail;
                        } else if (textStatus) {
                            errorMessage += ' ' + textStatus;
                        }
                        alert(errorMessage);
                    }
                });
            },
            true,
            null,
            false
        );
    });

    $(document).on('click', '.publish-version-btn', async function () {
        const versionId = $(this).data('id');
        const versionLabel = $(this).data('version');

        if (!confirm(`Publish version ${versionLabel} now? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`${apiBase}${versionId}/publish/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json().catch(function () {
                return {};
            });
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            reload();
        } catch (error) {
            alert(`Failed to publish version: ${error.message}`);
        }
    });

    let _removeVersionId = null;
    let _removeVersionRow = null;

    $(document).on('click', '.remove-version-btn', function () {
        _removeVersionId = $(this).data('id');
        _removeVersionRow = $(this).closest('tr');
        const label = $(this).data('version');
        $('#remove-version-message').text(
            `Remove published version ${label}? This will run in the background and cannot be undone.`
        );
        $('#btn-confirm-remove').prop('disabled', false).text('Remove');
        $('#remove-version-modal').modal('show');
    });

    $('#btn-confirm-remove').on('click', async function () {
        if (!_removeVersionId) return;
        const $btn = $(this);
        $btn.prop('disabled', true).text('Removing…');

        try {
            const response = await fetch(`${apiBase}${_removeVersionId}/delete/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json().catch(function () { return {}; });
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            $('#remove-version-modal').modal('hide');
            if (_removeVersionRow) {
                _removeVersionRow.remove();
                updateTableStateAfterRowRemoval();
            }
            $('#alertModalBody').html(data.message || 'Checklist removal queued.');
            $('#alertModal').modal({ keyboard: false, backdrop: 'static' });
        } catch (error) {
            $('#remove-version-modal').modal('hide');
            alert(`Failed to remove version: ${error.message}`);
        } finally {
            _removeVersionId = null;
            _removeVersionRow = null;
        }
    });

    $(document).on('click', '.delete-draft-btn', async function () {
        const $button = $(this);
        const versionId = $button.data('id');
        const versionLabel = $button.data('version');

        if (!confirm(`Delete draft version "${versionLabel}"? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`${apiBase}${versionId}/delete-draft/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json().catch(function () { return {}; });
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            $button.closest('tr').remove();
            updateTableStateAfterRowRemoval();
        } catch (error) {
            alert(`Failed to delete draft: ${error.message}`);
        }
    });

    $(document).on('click', '.edit-version-btn', function () {
        const $btn = $(this);
        $('#ev-id').val($btn.data('id'));
        $('#ev-doi').val($btn.data('doi'));
        $('#ev-notes').val($btn.data('notes'));
        $('#edit-version-error').addClass('d-none').text('');
        $('#edit-version-modal').modal('show');
    });

    $('#btn-save-edit').on('click', async function () {
        const versionId = $('#ev-id').val();
        const $btn = $(this);
        $btn.prop('disabled', true).text('Saving…');
        $('#edit-version-error').addClass('d-none').text('');

        try {
            const resp = await fetch(`${apiBase}${versionId}/update/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    doi: $('#ev-doi').val().trim(),
                    notes: $('#ev-notes').val().trim(),
                }),
            });
            const data = await resp.json().catch(function () { return {}; });
            if (!resp.ok) {
                $('#edit-version-error').text(data.detail || 'Save failed.').removeClass('d-none');
                return;
            }
            $('#edit-version-modal').modal('hide');
            reload();
        } catch (e) {
            $('#edit-version-error').text('Request failed: ' + e.message).removeClass('d-none');
        } finally {
            $btn.prop('disabled', false).text('Save');
        }
    });

    $(document).on('click', '.version-detail-link', async function (e) {
        e.preventDefault();
        const id = $(this).data('id');
        const $body = $('#version-detail-body');
        $('#version-detail-modal-label').text('Checklist Version');
        $body.html('<div class="text-center py-4"><span class="spinner-border spinner-border-sm"></span> Loading…</div>');
        $('#version-detail-modal').modal('show');

        try {
            const resp = await fetch(`${apiBase}${id}/`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
            const v = await resp.json();

            $('#version-detail-modal-label').text(`Version ${v.version}`);
            $body.html(`
                <dl class="row mb-0">
                    <dt class="col-sm-4">Module</dt>
                    <dd class="col-sm-8">${v.taxon_group_name || '—'}</dd>

                    <dt class="col-sm-4">Status</dt>
                    <dd class="col-sm-8">${statusBadge(v.status, v.is_publishing)}</dd>

                    <dt class="col-sm-4">Taxa</dt>
                    <dd class="col-sm-8">${v.status === 'published'
                        ? v.taxa_count
                        : '<span class="text-muted">— (snapshot created on publish)</span>'}</dd>

                    <dt class="col-sm-4">Changes</dt>
                    <dd class="col-sm-8">${changesBadge(v) || '—'}</dd>

                    <dt class="col-sm-4">DOI</dt>
                    <dd class="col-sm-8">${v.doi
                        ? `<a href="${v.doi}" target="_blank" rel="noopener">${v.doi}</a>`
                        : '—'}</dd>

                    <dt class="col-sm-4">Previous version</dt>
                    <dd class="col-sm-8">${v.previous_version || '—'}</dd>

                    <dt class="col-sm-4">Notes</dt>
                    <dd class="col-sm-8">${v.notes || '—'}</dd>

                    <dt class="col-sm-4">Created by</dt>
                    <dd class="col-sm-8">${v.created_by_name || '—'}</dd>

                    <dt class="col-sm-4">Created at</dt>
                    <dd class="col-sm-8">${fmtDate(v.created_at)}</dd>

                    <dt class="col-sm-4">Published by</dt>
                    <dd class="col-sm-8">${v.published_by_name || '—'}</dd>

                    <dt class="col-sm-4">Published at</dt>
                    <dd class="col-sm-8">${fmtDate(v.published_at)}</dd>
                </dl>
                ${(v.contributors && v.contributors.length) ? `
                <hr>
                <h6>Contributors</h6>
                <ul class="list-unstyled mb-0">
                    ${v.contributors.map(function (c) {
                        const name = (c.first_name || c.last_name)
                            ? `<strong>${escHtml(c.first_name)} ${escHtml(c.last_name)}</strong>`
                            : '<em class="text-muted">Organisation only</em>';
                        const org  = c.organisation ? ` &middot; ${escHtml(c.organisation)}` : '';
                        const email = c.email ? ` &middot; <a href="mailto:${escHtml(c.email)}">${escHtml(c.email)}</a>` : '';
                        const note = c.note ? ` <small class="text-muted">(${escHtml(c.note)})</small>` : '';
                        return `<li class="mb-1">${name}${org}${email}${note}</li>`;
                    }).join('')}
                </ul>` : ''}
            `);
        } catch (e) {
            $body.html(`<p class="text-danger">Failed to load: ${e.message}</p>`);
        }
    });
}(jQuery));
