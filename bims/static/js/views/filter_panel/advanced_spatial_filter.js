define([
    'backbone',
    'shared',
    'underscore',
    'jquery',
    'select2'
], function (Backbone, Shared, _, $, select2) {

    return Backbone.View.extend({
        template: _.template($('#advanced-spatial-filter-template').html()),

        DATA: {},
        // Maps field display name → child key (e.g. "SA KBA Name" → "902d304a...kba_name")
        FIELD_KEYS: {},
        // Maps field key → { layer_name, wms_url, wms_format, layer_identifier }
        LAYER_META: {},
        // For fields with autocomplete children, store their group keys
        AUTOCOMPLETE_FIELDS: {},

        FIELDS_WITH_ALL: null,
        ALL_ID: "__ALL__",
        ALL_TEXT: "All",

        groups: null,
        groupSeq: 0,
        clauseSeq: 0,
        dataLoaded: false,

        events: {
            'click .adv-add-group': 'onAddGroupClick',
        },

        initialize: function (options) {
            this.parent = options.parent;
            this.groups = [];
            this.groupSeq = 0;
            this.clauseSeq = 0;
            this.dataLoaded = false;
            this.DATA = {};
            this.FIELD_KEYS = {};
            this.LAYER_META = {};
            this.AUTOCOMPLETE_FIELDS = {};
            this.FIELDS_WITH_ALL = new Set();
        },

        render: function () {
            this.$el.html(this.template());
            this.$groups = this.$el.find('.adv-groups');
            this.$preview = this.$el.find('.adv-preview');
            this.$addGroupBtn = this.$el.find('.adv-add-group');
            this.$addGroupBtn.prop('disabled', true);
            this.refreshPreview();
            this.getSpatialScaleFilter();
            return this;
        },

        getSpatialScaleFilter: function () {
            var self = this;
            $.ajax({
                type: 'GET',
                url: '/api/spatial-scale-filter-list/',
                dataType: 'json',
                success: function (data) {
                    self.parseSpatialScaleData(data);
                    if (self.pendingRestore) {
                        self._doRestore(self.pendingRestore);
                        self.pendingRestore = null;
                    } else {
                        self.addGroup();
                    }
                }
            });
        },

        parseSpatialScaleData: function (data) {
            var self = this;
            self.DATA = {};
            self.FIELD_KEYS = {};
            self.LAYER_META = {};
            self.AUTOCOMPLETE_FIELDS = {};
            self.FIELDS_WITH_ALL = new Set();

            $.each(data, function (index, spatialData) {
                if (!spatialData.hasOwnProperty('children')) {
                    return true;
                }

                // Each child becomes its own field
                $.each(spatialData['children'], function (ci, child) {
                    var fieldName = child['name'];
                    var childKey = child['key'];

                    // Store layer metadata for boundary display
                    self.LAYER_META[childKey] = {
                        layer_name: child['layer_name'] || '',
                        wms_url: child['wms_url'] || '',
                        wms_format: child['wms_format'] || '',
                        layer_identifier: child['layer_identifier'] || ''
                    };

                    if (child['autocomplete']) {
                        self.DATA[fieldName] = [];
                        self.FIELD_KEYS[fieldName] = childKey;
                        self.FIELDS_WITH_ALL.add(fieldName);
                        self.AUTOCOMPLETE_FIELDS[fieldName] = [childKey];
                    } else if (child['value'] && child['value'].length > 0) {
                        var values = [];
                        $.each(child['value'], function (vi, val) {
                            if (val['query'] && values.indexOf(val['query']) === -1) {
                                values.push(val['query']);
                            }
                        });
                        if (values.length > 0) {
                            self.DATA[fieldName] = values;
                            self.FIELD_KEYS[fieldName] = childKey;
                            self.FIELDS_WITH_ALL.add(fieldName);
                        }
                    }
                });
            });

            self.dataLoaded = true;
            self.$addGroupBtn.prop('disabled', false);
        },

        // ---- Field helpers ----
        allFields: function () {
            return Object.keys(this.DATA);
        },

        usedFieldsInGroup: function (group) {
            return group.clauses.map(function (c) { return c.field; });
        },

        usedFieldsGlobal: function () {
            var result = [];
            for (var i = 0; i < this.groups.length; i++) {
                var clauses = this.groups[i].clauses;
                for (var j = 0; j < clauses.length; j++) {
                    result.push(clauses[j].field);
                }
            }
            return result;
        },

        firstUnusedGlobal: function () {
            var used = this.usedFieldsGlobal();
            var fields = this.allFields();
            for (var i = 0; i < fields.length; i++) {
                if (used.indexOf(fields[i]) === -1) return fields[i];
            }
            return null;
        },

        firstUnusedForGroup: function (group) {
            var globalUsed = this.usedFieldsGlobal();
            var groupUsed = this.usedFieldsInGroup(group);
            var fields = this.allFields();
            for (var i = 0; i < fields.length; i++) {
                if (globalUsed.indexOf(fields[i]) === -1 &&
                    groupUsed.indexOf(fields[i]) === -1) {
                    return fields[i];
                }
            }
            return null;
        },

        getOptionsForField: function (field) {
            var data = this.DATA[field] || [];
            var base = data.map(function (v) { return { id: v, text: v }; });
            if (this.FIELDS_WITH_ALL.has(field)) {
                return [{ id: this.ALL_ID, text: this.ALL_TEXT }].concat(base);
            }
            return base;
        },

        isAllSelected: function (vals) {
            return Array.isArray(vals) && vals.indexOf(this.ALL_ID) > -1;
        },

        quote: function (s) {
            return '"' + String(s).replace(/"/g, '\\"') + '"';
        },

        clauseToHuman: function (c) {
            var self = this;
            if (!c.values || !c.values.length) return '';
            if (this.isAllSelected(c.values)) return c.field + ': ' + this.ALL_TEXT;
            if (c.values.length === 1) return c.field + ' = ' + this.quote(c.values[0]);
            return c.field + ' IN [' + c.values.map(function (v) { return self.quote(v); }).join(', ') + ']';
        },

        clauseToExpr: function (c) {
            if (!c.values || !c.values.length) return '';
            if (this.isAllSelected(c.values)) return 'TRUE';
            if (c.values.length === 1) return c.field + ' == ' + JSON.stringify(c.values[0]);
            return '(' + c.values.map(function (v) {
                return c.field + ' == ' + JSON.stringify(v);
            }).join(' OR ') + ')';
        },

        toHuman: function () {
            var self = this;
            var parts = this.groups.map(function (g) {
                var bits = g.clauses.map(function (c) {
                    return self.clauseToHuman(c);
                }).filter(Boolean);
                if (bits.length === 0) return '';
                var joined = bits.join(' OR ');
                return bits.length > 1 ? '(' + joined + ')' : joined;
            }).filter(Boolean);
            return parts.length ? parts.join(' AND ') : '\u2014 (no filters) \u2014';
        },

        toExpr: function () {
            var self = this;
            var parts = this.groups.map(function (g) {
                var bits = g.clauses.map(function (c) {
                    return self.clauseToExpr(c);
                }).filter(Boolean);
                if (!bits.length) return '';
                var joined = bits.join(' OR ');
                return bits.length > 1 ? '(' + joined + ')' : joined;
            }).filter(Boolean);
            return parts.join(' AND ');
        },

        refreshPreview: function () {
            if (!this.$preview) return;
            this.$preview.text(this.toHuman());
            if (this.onChanged) this.onChanged();
        },

        // ---- Field disable management ----
        refreshAllFieldDisables: function () {
            var self = this;
            var used = self.usedFieldsGlobal();
            var usedSet = {};
            for (var u = 0; u < used.length; u++) usedSet[used[u]] = true;

            this.$el.find('.adv-clause').each(function () {
                var $c = $(this);
                var cid = Number($c.attr('data-cid'));
                var clause = self.findClauseById(cid);
                if (!clause) return;

                var fields = self.allFields();
                var opts = '';
                for (var i = 0; i < fields.length; i++) {
                    var disabled = (usedSet[fields[i]] && fields[i] !== clause.field) ? 'disabled' : '';
                    var selected = (fields[i] === clause.field) ? 'selected' : '';
                    opts += '<option value="' + fields[i] + '" ' + disabled + ' ' + selected + '>' + fields[i] + '</option>';
                }
                $c.find('.adv-field-select').html(opts);
            });

            this.$el.find('.adv-group').each(function () {
                var $g = $(this);
                var gid = Number($g.attr('data-gid'));
                var group = self.findGroupById(gid);
                if (!group) return;
                var hasUnused = !!self.firstUnusedForGroup(group);
                $g.find('.adv-btn-add-clause').prop('disabled', !hasUnused);
            });

            this.$addGroupBtn.prop('disabled', !this.firstUnusedGlobal());
        },

        findGroupById: function (gid) {
            for (var i = 0; i < this.groups.length; i++) {
                if (this.groups[i].id === gid) return this.groups[i];
            }
            return null;
        },

        findClauseById: function (cid) {
            for (var i = 0; i < this.groups.length; i++) {
                var clauses = this.groups[i].clauses;
                for (var j = 0; j < clauses.length; j++) {
                    if (clauses[j].id === cid) return clauses[j];
                }
            }
            return null;
        },

        makeClause: function (field, values) {
            return {
                id: ++this.clauseSeq,
                field: field,
                key: this.FIELD_KEYS[field] || '',
                values: values ? values.slice() : []
            };
        },

        // ---- Select2 builder for clause values ----
        buildValuesSelect: function ($wrap, clause) {
            var self = this;
            var $old = $wrap.find('.adv-values-wrap');
            if ($old.length) $old.remove();

            var $valuesWrap = $('<div class="adv-values-wrap"></div>');
            var $select = $('<select multiple="multiple" style="width:100%"></select>');
            $valuesWrap.append($select);
            $wrap.append($valuesWrap);

            let fullOptions = self.getOptionsForField(clause.field);
            let autocompleteKeys = self.AUTOCOMPLETE_FIELDS[clause.field];

            // If this field has autocomplete children, use AJAX Select2
            if (autocompleteKeys && autocompleteKeys.length > 0) {
                self.buildAjaxValuesSelect($select, clause, fullOptions, autocompleteKeys);
                return;
            }

            function mountSelect(options, selectedVals) {
                try { $select.select2('destroy'); } catch (e) {}
                $select.empty();
                for (var i = 0; i < options.length; i++) {
                    $select.append(new Option(options[i].text, options[i].id, false, false));
                }
                $select.select2({
                    data: options,
                    placeholder: 'Add ' + clause.field + '\u2026',
                    allowClear: true,
                    width: 'resolve'
                });
                if (selectedVals && selectedVals.length) {
                    $select.val(selectedVals).trigger('change', { programmatic: true });
                }
            }

            mountSelect(fullOptions, clause.values);

            $select.on('change', function (_e, meta) {
                if (meta && meta.programmatic) return;

                let vals = $(this).val() || [];

                if (self.isAllSelected(vals) && !self.isAllSelected(clause.values)) {
                    vals = [self.ALL_ID];
                    clause.values = vals;
                    $select.val(vals).trigger('change', { programmatic: true });
                    self.refreshPreview();
                } else {
                    if (clause.values.indexOf(self.ALL_ID) > -1) {
                        if (vals.indexOf(self.ALL_ID) > -1) vals.splice(vals.indexOf(self.ALL_ID), 1);
                        $select.val(vals).trigger('change', { programmatic: true });
                    }
                    clause.values = vals;
                    self.refreshPreview();
                }
            });
        },

        // AJAX-based Select2 for fields with autocomplete children
        buildAjaxValuesSelect: function ($select, clause, localOptions, autocompleteKeys) {
            var self = this;
            for (var i = 0; i < localOptions.length; i++) {
                $select.append(new Option(localOptions[i].text, localOptions[i].id, false, false));
            }

            let autocompleteKeyParams = autocompleteKeys[0].split('.');
            if (autocompleteKeyParams.length < 2) {
                return false;
            }

            $select.select2({
                placeholder: 'Search ' + clause.field + '\u2026',
                allowClear: true,
                width: 'resolve',
                ajax: {
                    url: '/location-context-autocomplete/',
                    dataType: 'json',
                    delay: 250,
                    data: function (params) {
                        return {
                            q: params.term,
                            groupKey: autocompleteKeyParams[0],
                            layerIdentifier: autocompleteKeyParams[1]
                        };
                    },
                    processResults: function (data) {
                        let results = [];
                        if (self.FIELDS_WITH_ALL.has(clause.field)) {
                            results.push({ id: self.ALL_ID, text: self.ALL_TEXT });
                        }
                        $.each(data, function (idx, obj) {
                            results.push({ id: obj.value, text: obj.value });
                        });
                        return { results: results };
                    },
                    cache: true
                },
                minimumInputLength: 0
            });

            // Set initial values if any
            if (clause.values && clause.values.length) {
                for (var v = 0; v < clause.values.length; v++) {
                    var val = clause.values[v];
                    var text = (val === self.ALL_ID) ? self.ALL_TEXT : val;
                    if ($select.find('option[value="' + val + '"]').length === 0) {
                        $select.append(new Option(text, val, true, true));
                    }
                }
                $select.trigger('change', { programmatic: true });
            }

            $select.on('change', function (_e, meta) {
                if (meta && meta.programmatic) return;

                let vals = $(this).val() || [];

                if (self.isAllSelected(vals) && !self.isAllSelected(clause.values)) {
                    vals = [self.ALL_ID];
                    clause.values = vals;
                    $select.val(vals).trigger('change', { programmatic: true });
                    self.refreshPreview();
                } else {
                    if (clause.values.indexOf(self.ALL_ID) > -1) {
                        if (vals.indexOf(self.ALL_ID) > -1) vals.splice(vals.indexOf(self.ALL_ID), 1);
                        $select.val(vals).trigger('change', { programmatic: true });
                    }
                    clause.values = vals;
                    self.refreshPreview();
                }
            });
        },

        // ---- Render a single clause ----
        renderClause: function (group, clause) {
            var self = this;
            var used = self.usedFieldsGlobal();
            var usedSet = {};
            for (var u = 0; u < used.length; u++) usedSet[used[u]] = true;

            var fields = self.allFields();
            var fieldOptions = '';
            for (var i = 0; i < fields.length; i++) {
                var disabled = (usedSet[fields[i]] && fields[i] !== clause.field) ? 'disabled' : '';
                var selected = (fields[i] === clause.field) ? 'selected' : '';
                fieldOptions += '<option value="' + fields[i] + '" ' + disabled + ' ' + selected + '>' + fields[i] + '</option>';
            }

            var $c = $('<div class="adv-clause" data-cid="' + clause.id + '">' +
                '<div class="adv-clause-header">' +
                    '<select class="adv-field-select">' + fieldOptions + '</select>' +
                    '<button class="btn btn-sm adv-btn-remove-clause" type="button" title="Remove Filter">' +
                        '<i class="fa fa-trash"></i>' +
                    '</button>' +
                '</div>' +
                '<div class="adv-clause-note"></div>' +
            '</div>');

            $c.on('change', '.adv-field-select', function () {
                var $sel = $(this);
                var nextField = $sel.val();

                var alreadyUsed = false;
                for (var gi = 0; gi < self.groups.length; gi++) {
                    var cls = self.groups[gi].clauses;
                    for (var ci = 0; ci < cls.length; ci++) {
                        if (cls[ci].field === nextField && cls[ci].id !== clause.id) {
                            alreadyUsed = true;
                            break;
                        }
                    }
                    if (alreadyUsed) break;
                }

                if (alreadyUsed) {
                    $sel.val(clause.field);
                    var $note = $c.find('.adv-clause-note');
                    $note.text('Field "' + nextField + '" is already used in another filter.');
                    setTimeout(function () { $note.text(''); }, 1800);
                    return;
                }

                clause.field = nextField;
                clause.key = self.FIELD_KEYS[nextField] || '';
                clause.values = [];
                self.buildValuesSelect($c, clause);
                self.refreshPreview();
                self.refreshAllFieldDisables();
            });

            $c.on('click', '.adv-btn-remove-clause', function () {
                group.clauses = group.clauses.filter(function (cl) {
                    return cl.id !== clause.id;
                });
                $c.remove();
                self.refreshPreview();
                self.refreshAllFieldDisables();
            });

            self.buildValuesSelect($c, clause);
            return $c;
        },

        // ---- Render a group ----
        renderGroup: function (group) {
            var self = this;

            var $g = $('<div class="adv-group" data-gid="' + group.id + '">' +
                '<div class="adv-group-header">' +
                    '<button class="btn btn-sm adv-btn-remove-group" type="button"><i class="fa fa-times"></i></button>' +
                    '<span class="adv-group-title">Filter Group</span>' +
                    '<span style="flex:1"></span>' +
                    '<button class="btn btn-sm adv-btn-add-clause adv-spatial-filter-btn" type="button">+ Add Filter</button>' +
                '</div>' +
                '<div class="adv-clauses"></div>' +
            '</div>');

            var $clauses = $g.find('.adv-clauses');

            for (var i = 0; i < group.clauses.length; i++) {
                $clauses.append(self.renderClause(group, group.clauses[i]));
            }

            $g.on('click', '.adv-btn-add-clause', function () {
                var f = self.firstUnusedForGroup(group);
                if (!f) return;
                var cl = self.makeClause(f, []);
                group.clauses.push(cl);
                $clauses.append(self.renderClause(group, cl));
                self.refreshPreview();
                self.refreshAllFieldDisables();
            });

            $g.on('click', '.adv-btn-remove-group', function () {
                self.groups = self.groups.filter(function (gr) {
                    return gr.id !== group.id;
                });
                $g.remove();
                self.refreshPreview();
                self.refreshAllFieldDisables();
            });

            return $g;
        },

        addGroup: function (initial) {
            var initialField = this.firstUnusedGlobal() || this.allFields()[0];
            var group;

            if (initial && initial.clauses) {
                var self = this;
                group = {
                    id: ++this.groupSeq,
                    clauses: initial.clauses.map(function (c) {
                        return self.makeClause(c.field, c.values);
                    })
                };
            } else {
                group = {
                    id: ++this.groupSeq,
                    clauses: [this.makeClause(initialField, [])]
                };
            }

            this.groups.push(group);
            this.$groups.append(this.renderGroup(group));
            this.refreshPreview();
            this.refreshAllFieldDisables();
        },

        onAddGroupClick: function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (!this.dataLoaded) return;
            this.addGroup();
        },

        // ---- Public interface ----
        getSelected: function () {
            return {
                expression: this.toExpr(),
                human: this.toHuman(),
                groups: this.groups
            };
        },

        hasFilters: function () {
            for (var i = 0; i < this.groups.length; i++) {
                var clauses = this.groups[i].clauses;
                for (var j = 0; j < clauses.length; j++) {
                    if (clauses[j].values && clauses[j].values.length > 0) {
                        return true;
                    }
                }
            }
            return false;
        },

        /**
         * Restore groups from URL/saved data.
         * If data hasn't loaded yet, queues the restore for after load.
         * @param {Array} groupsData - array of group objects with clauses
         */
        restoreGroups: function (groupsData) {
            if (!this.dataLoaded) {
                this.pendingRestore = groupsData;
                return;
            }
            this._doRestore(groupsData);
        },

        _doRestore: function (groupsData) {
            var self = this;
            // Clear existing groups
            this.groups = [];
            this.groupSeq = 0;
            this.clauseSeq = 0;
            this.$groups.empty();

            // Build a reverse map: key → field name
            var keyToField = {};
            var fields = Object.keys(this.FIELD_KEYS);
            for (var i = 0; i < fields.length; i++) {
                keyToField[this.FIELD_KEYS[fields[i]]] = fields[i];
            }

            for (var g = 0; g < groupsData.length; g++) {
                var savedGroup = groupsData[g];
                if (!savedGroup.clauses || !savedGroup.clauses.length) continue;
                var clauses = [];
                for (var c = 0; c < savedGroup.clauses.length; c++) {
                    var sc = savedGroup.clauses[c];
                    // Resolve field name from key if field is missing
                    var field = sc.field || keyToField[sc.key] || '';
                    if (!field) continue;
                    clauses.push({ field: field, values: sc.values || [] });
                }
                if (clauses.length > 0) {
                    this.addGroup({ clauses: clauses });
                }
            }

            // If nothing was restored, add a default empty group
            if (this.groups.length === 0) {
                this.addGroup();
            }
        },

        clearAll: function () {
            this.groups = [];
            this.groupSeq = 0;
            this.clauseSeq = 0;
            this.$groups.empty();
            this.addGroup();
        },

        /**
         * Returns selected filter layers and their metadata for boundary display.
         * Format: { layers: { key: [values] }, meta: { key: { layer_name, wms_url, ... } } }
         */
        getSelectedLayers: function () {
            var self = this;
            var layers = {};
            for (var i = 0; i < this.groups.length; i++) {
                var clauses = this.groups[i].clauses;
                for (var j = 0; j < clauses.length; j++) {
                    var c = clauses[j];
                    if (!c.values || !c.values.length || !c.key) continue;
                    if (self.isAllSelected(c.values)) {
                        layers[c.key] = ['__group__'];
                    } else {
                        layers[c.key] = c.values.slice();
                    }
                }
            }
            return { layers: layers, meta: self.LAYER_META };
        }

    });
});
