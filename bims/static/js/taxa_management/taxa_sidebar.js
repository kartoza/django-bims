export const taxaSidebar = (() => {
    const $addNewModuleBtn = $('.add-new-module');
    const $taxonGroupCard = $('.ui-state-default');
    const $updateBtn = $('.update-logo-btn');
    const $editTaxonGroupModal = $('#editModuleModal');
    const $removeAllBtn = $('.remove-all-btn');

    const $removeModuleName = $('#remove-module-name');
    const $removeModuleBtn = $('#remove-module-btn');

    let currentRemoveModuleName = '';
    let selectedTaxonGroup = '';
    let updateTaxonGroup = null;

    function findGbifTaxonomyByTaxonGroupId(parentId, groups) {
        let item = groups.find(item => item.id === parentId && item.gbif_parent_species);
        if (item) {
            item = JSON.parse(item.gbif_parent_species)
        }
        if (!item) {
            for (let i = 0; i < groups.length; i++) {
                let group = groups[i];
                if (group.children.length > 0) {
                    item = findGbifTaxonomyByTaxonGroupId(parentId, group.children)
                }
                if (item) {
                    break;
                }
            }
        }
        return item ? item : null;
    }
    function findSelectedParent(taxonGroups, childId) {
        let result = null;

        function search(items) {
            for (let item of items) {
                if (item.children && item.children.some(child => child.id === childId)) {
                    result = { ...item };
                    delete result.children;
                    return true;
                }
                if (item.children && item.children.length > 0) {
                    if (search(item.children)) {
                        return true;
                    }
                }
            }
            return false;
        }

        search(taxonGroups);
        return result;
    }

    function findExpertsByTaxonGroupId(parentId, taxonGroups) {
        let experts = [];
        taxonGroups.forEach(item => {
            if (item.children.length > 0) {
                experts = findExpertsByTaxonGroupId(parentId, item.children);
            }
            if (item.id === parentId && item.experts.length > 0) {
                experts = item.experts;
            }
            if (experts.length > 0) {
                return true;
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

    function setupAddModuleModal() {
        $('#moduleModalLabel').text('Add Module');
        $('.gbif-species-container').hide();
        $('#edit-module-id').val('');
        $('#edit-module-name').val('');
        $("#inputLogo").val('');
        $('.extra-attribute-field').empty();
        $('.taxon-group-experts-container select').val(null).trigger('change');
        $('#edit-module-img-container').empty();

        $('#editModuleModal').modal({
            keyboard: false
        });
    }

    function handleAddNewModuleSelected(event) {
        event.preventDefault();
        setupAddModuleModal();
    }

    function handleTaxonGroupSelected(event) {
        let $elm = $(event.target);
        let maxTry = 10;
        let currentTry = 1;
        while (!$elm.hasClass('ui-state-default') && currentTry < maxTry) {
            currentTry++;
            $elm = $elm.parent();
        }
        $('.ui-state-default').removeClass('selected');
        $elm.addClass('selected');
        if (updateTaxonGroup) {
            updateTaxonGroup($elm.data('id'));
        }
        // selectedTaxonGroup = $elm.data('id');
        // $('#taxon-name-input').val('');
        // insertParam('selected', selectedTaxonGroup);
    }

    function allTaxaGroups(groups) {
        let allGroups = [];
        for (let taxaGroup of groups) {
            if (taxaGroup.children && taxaGroup.children.length > 0) {
                allGroups.push(...allTaxaGroups(taxaGroup.children))
            }
            allGroups.push(taxaGroup)
        }
        return allGroups
    }

    function filterTaxaGroups(taxaGroups, moduleId) {
        let clone = JSON.parse(JSON.stringify(taxaGroups))
        return allTaxaGroups(clone).filter(
            taxon => parseInt(taxon.id) !== parseInt(moduleId));
    }

    function handleUpdateTaxonGroupSelected(event) {
        event.preventDefault();
        event.stopPropagation();
        $('#moduleModalLabel').text('Edit Module');
        $('.gbif-species-container').show();
        const _maxTries = 10;
        let _element = $(event.target);
        let _currentTry = 1
        while (!_element.data('id') && _currentTry < _maxTries) {
            _element = _element.parent();
            _currentTry += 1;
        }
        const moduleId = _element.data('id');
        $editTaxonGroupModal.data('module', moduleId);

        const moduleName = _element.find('.taxon-group-name').html().trim();
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
        $editTaxonGroupModal.modal({
            keyboard: false
        })
        // Experts
        authorSelect.empty();
        authorSelect.val(null).trigger('change');
        let experts = findExpertsByTaxonGroupId(moduleId, taxaGroups);
        addExpertsToSelect(experts);

        // GBIF Species
        let taxaAutoComplete = $('#edit-module-taxa-autocomplete');
        taxaAutoComplete.empty();
        taxaAutoComplete.val(null).trigger('change');
        let gbifSpecies = findGbifTaxonomyByTaxonGroupId(moduleId, taxaGroups);
        if (gbifSpecies) {
            let option = new Option(`${gbifSpecies['canonical_name']} (${gbifSpecies['rank']})`, gbifSpecies.id, true, true);
            taxaAutoComplete.append(option).trigger('change');
            taxaAutoComplete.trigger({
                type: 'select2:select',
            });
        }

        // Parent taxa group selection
        const selectedParent = findSelectedParent(
            taxaGroups, moduleId
        )
        const filteredTaxaGroups = filterTaxaGroups(taxaGroups, moduleId)
        let selectHTML = $(
            '<select class="form-control" name="parent-taxon" id="parent-taxon-select"></select>');
        selectHTML.append($('<option>').val('').text('Select a Parent Taxon'));
        filteredTaxaGroups.forEach(function(taxon) {
            let option = $('<option>').val(taxon.id).text(taxon.name);
            selectHTML.append(option);
        });
        if (selectedParent) {
            selectHTML.val(selectedParent.id).change()
        }
        $('#parent-taxon-module-container').html(selectHTML);

        // Upload template
        let taxaUploadTemplate = _element.find('.taxon-group-title').data('taxa-upload-template');
        $editTaxonGroupModal.find('#taxa-upload-template-link').attr('href', taxaUploadTemplate);
        $editTaxonGroupModal.find('#taxa-upload-template-link').text(taxaUploadTemplate.split('/').pop());

        let occurrenceUploadTemplate = _element.find('.taxon-group-title').data('occurrence-upload-template');
        $editTaxonGroupModal.find('#occurrence-upload-template-link').attr('href', occurrenceUploadTemplate);
        $editTaxonGroupModal.find('#occurrence-upload-template-link').text(occurrenceUploadTemplate.split('/').pop());


        return false;
    }

    function handleAllRemoveAll(event) {
        event.preventDefault();
        event.stopPropagation();
        $removeModuleBtn.attr('disabled', true);
        const _maxTries = 10;
        let _element = $(event.target);
        let _currentTry = 1
        while (!_element.hasClass('ui-state-default') && _currentTry < _maxTries) {
            _element = _element.parent();
            _currentTry += 1;
        }
        currentRemoveModuleName = _element.find('.taxon-group-name').html().trim();
        $removeModuleName.val('');
        $('#remove-module-btn').attr('data-module-id', _element.data('id'));
        $('#removeModuleModal').modal({
            keyboard: false
        })
        return false;
    }

    function handleRemoveModuleNameChanged(event) {
        if ($removeModuleName.val() === currentRemoveModuleName) {
            $removeModuleBtn.attr('disabled', false);
        } else {
            $removeModuleBtn.attr('disabled', true);
        }
    }

    function handleSubmitRemoveModule(event) {
        event.preventDefault();
        $removeModuleBtn.html('Processing...')
        $removeModuleBtn.attr('disabled', true)
        const moduleId = $(event.target).data('module-id');
        const url = `/api/remove-occurrences/?taxon_module=${moduleId}`

        // Show the processing modal
        $('#processingModal').modal({
            backdrop: 'static',
            keyboard: false,
            show: true
        });

        $.ajax({
            type: 'GET',
            headers: {"X-CSRFToken": csrfToken},
            url: url,
            cache: false,
            contentType: false,
            processData: false,
            success: function (data) {
                const taskId = data.task_id;
                checkTaskStatus(taskId);
            },
            error: function (data) {
                console.log("error");
                console.log(data);
                $removeModuleBtn.html('Remove Module');
                $removeModuleBtn.attr('disabled', false);
                // Hide the processing modal
                $('#processingModal').modal('hide');
            }
        });
    }

    function checkTaskStatus(taskId) {
        const url = `/api/celery-status/${taskId}/`;

        $.ajax({
            type: 'GET',
            url: url,
            success: function (data) {
                if (data.state === 'PENDING' || data.state === 'STARTED') {
                    setTimeout(function () {
                        checkTaskStatus(taskId);
                    }, 2000); // check again after 2 seconds
                } else if (data.state === 'SUCCESS') {
                    location.reload();
                } else {
                    console.log("Task failed or was revoked.");
                    $removeModuleBtn.html('Remove Module');
                    $removeModuleBtn.attr('disabled', false);
                    // Hide the processing modal
                    $('#processingModal').modal('hide');
                }
            },
            error: function (data) {
                console.log("error");
                console.log(data);
                $removeModuleBtn.html('Remove Module');
                $removeModuleBtn.attr('disabled', false);
                // Hide the processing modal
                $('#processingModal').modal('hide');
            }
        });
    }

    function handleAddExtraAttribute(event) {
        event.preventDefault();
        const extraAttributesContainer = $('#editModuleModal').find('.extra-attribute-field');
        let exAtEl = '<div style="display: flex" >' +
            '<input aria-label="extra-attribute" type="text" class="form-control" name="extra_attribute" value="" />' +
            '<button class="btn btn-danger remove-extra-attribute">-</button>' +
            '</div>';
        extraAttributesContainer.append(exAtEl);
    }

    function handleRemoveExtraAttribute(event) {
        event.preventDefault();
        $(event.target).parent().remove();
    }

    function handleSubmitModuleEdit(e) {
        e.preventDefault();
        let formData = new FormData(this);
        formData.delete('taxon-group-experts');

        $('.owner-auto-complete').select2('data').forEach(function(item) {
            formData.append('taxon-group-experts', item.id);
        });

        let url = '/api/update-taxon-group/';
        $(e.target).find('.btn-submit').prop('disabled', true);
        $(e.target).find('.btn-submit-text').html('');
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
                $(e.target).find('.btn-submit-text').html('Save');
                console.log("error");
                console.log(data);
            }
        });
    }

    function init(_updateTaxonGroup, _selectedTaxonGroup) {
        $addNewModuleBtn.on('click', handleAddNewModuleSelected)
        $taxonGroupCard.on('click', handleTaxonGroupSelected)
        $updateBtn.on('click', handleUpdateTaxonGroupSelected)
        $removeAllBtn.on('click', handleAllRemoveAll)
        $removeModuleName.on('input', handleRemoveModuleNameChanged)
        $removeModuleBtn.on('click', handleSubmitRemoveModule)

        $('#moduleEditForm').on('submit', handleSubmitModuleEdit)
        $('.btn-add-extra-attribute').on('click', handleAddExtraAttribute)
        $(document).on('click', '.remove-extra-attribute', function(e) {
            handleRemoveExtraAttribute(e)
        })

        selectedTaxonGroup = _selectedTaxonGroup
        updateTaxonGroup = _updateTaxonGroup
    }

    return {
        init,
        allTaxaGroups
    };
})();
