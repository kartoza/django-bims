define([
    'backbone',
    'shared',
    'underscore'
], function (Backbone, Shared, _) {

    return Backbone.View.extend({
        template: _.template($('#taxon-tags-template').html()),

        events: {
            'click .subtitle': 'togglePanel',
            'click .apply-filter': 'onApplyClick',
            'click .clear-filter': 'onClearClick'
        },

        initialize: function (options) {
            _.bindAll(
                this,
                'render',
                'initSelect2',
                'setInitialSelection',
                'bootstrapTagsByIds',
                'applyOptionsToSelect',
                'getSelected',
                'highlight',
                'togglePanel',
                'onApplyClick',
                'onClearClick',
                'initPopovers'
            );

            this.parent = options.parent;
            this.dropdownEl = null;
            this.bodyRowEl = null;
            this.isOpen = false;
            this.tagDescriptions = {}; // Cache for tag descriptions

            this.parent.filtersReady['taxonTags'] = false;
        },

        render: function () {
            this.$el.html(this.template());

            this.dropdownEl = this.$el.find('#taxon-tags-search');
            this.bodyRowEl = this.$el.find('.row').eq(1);

            this.initSelect2();

            this.setInitialSelection();

            return this;
        },

        initSelect2: function () {
            var self = this;

            this.dropdownEl.select2({
                width: '100%',
                multiple: true,
                placeholder: 'Choose a tag',
                allowClear: true,

                ajax: {
                    url: '/api/taxon-tag-autocomplete/',
                    dataType: 'json',
                    delay: 250,
                    data: function (params) {
                        return {
                            q: params.term || ''
                        };
                    },
                    processResults: function (data) {
                        var results = [];
                        for (var i = 0; i < data.length; i++) {
                            var description = data[i].description || '';
                            // Store description in cache
                            if (description) {
                                self.tagDescriptions[data[i].id] = description;
                            }
                            results.push({
                                id: data[i].id,
                                text: data[i].name,
                                description: description
                            });
                        }
                        return { results: results };
                    },
                    cache: true
                },

                closeOnSelect: false,

                templateSelection: function (item, container) {
                    var text = item.text || item.name || item.id;
                    // Get description from item or from cache
                    var description = item.description || self.tagDescriptions[item.id] || '';

                    if (description) {
                        var $el = $('<span class="taxon-tag-selection">' + text +
                            '<i class="fa fa-info-circle taxon-tag-info" data-description="' +
                            description.replace(/"/g, '&quot;') + '"></i></span>');
                        return $el;
                    }
                    return text;
                },

                templateResult: function (item) {
                    if (item.loading) {
                        return item.text;
                    }
                    return item.text || item.name || item.id;
                }
            });
            this.dropdownEl.on('select2:select select2:unselect', function() {
                self.initPopovers();
            });
            this.dropdownEl.on('change', function() {
                setTimeout(function() {
                    self.initPopovers();
                }, 50);
            });
        },

        initPopovers: function() {
            var container = $('#map-container').length ? '#map-container' : 'body';
            this.$el.find('.taxon-tag-info').each(function() {
                var $icon = $(this);
                var description = $icon.data('description');
                if (description) {
                    try {
                        $icon.popover('dispose');
                    } catch (e) {
                    }
                    $icon.popover({
                        content: description,
                        placement: 'top',
                        container: container,
                        trigger: 'hover focus'
                    });
                }
            });
        },

        setInitialSelection: function () {
            var self = this;
            var initial = this.parent.initialSelectedTaxonTags || [];
            if (!initial.length) {
                this.parent.filtersReady['taxonTags'] = true;
                this.highlight(false);
                return;
            }

            var knownOptions = [];
            var unknownIds = [];

            for (var i = 0; i < initial.length; i++) {
                var tagItem = initial[i];

                if (typeof tagItem === 'object' && tagItem !== null) {
                    if (tagItem.id !== undefined) {
                        knownOptions.push({
                            id: tagItem.id,
                            text: tagItem.name || ('' + tagItem.id)
                        });
                    }
                } else {
                    unknownIds.push(tagItem);
                }
            }

            if (knownOptions.length) {
                this.applyOptionsToSelect(knownOptions);
            }

            if (unknownIds.length) {
                this.bootstrapTagsByIds(unknownIds).done(function (resolvedOptions) {
                    self.applyOptionsToSelect(resolvedOptions);

                    self.parent.filtersReady['taxonTags'] = true;
                    self.highlight(self.getSelected().length > 0);
                }).fail(function () {
                    self.parent.filtersReady['taxonTags'] = true;
                    self.highlight(self.getSelected().length > 0);
                });
            } else {
                this.parent.filtersReady['taxonTags'] = true;
                this.highlight(this.getSelected().length > 0);
            }
        },

        /**
         * Hit /api/taxon-tag-autocomplete/?ids=1,4,9
         * and convert to [{id:1,text:"Terrestrial",description:"..."}, ...]
         */
        bootstrapTagsByIds: function (idsArray) {
            var dfd = $.Deferred();
            var self = this;

            var uniqueIds = [];
            for (var i = 0; i < idsArray.length; i++) {
                var v = idsArray[i];
                if ($.inArray(v, uniqueIds) === -1) {
                    uniqueIds.push(v);
                }
            }

            $.ajax({
                url: '/api/taxon-tag-autocomplete/',
                dataType: 'json',
                data: {
                    ids: uniqueIds.join(',')
                },
                success: function (data) {
                    var opts = [];
                    for (var j = 0; j < data.length; j++) {
                        var description = data[j].description || '';
                        // Store description in cache
                        if (description) {
                            self.tagDescriptions[data[j].id] = description;
                        }
                        opts.push({
                            id: data[j].id,
                            text: data[j].name,
                            description: description
                        });
                    }
                    dfd.resolve(opts);
                },
                error: function () {
                    dfd.reject();
                }
            });

            return dfd.promise();
        },

        applyOptionsToSelect: function (optionsList) {
            var self = this;
            for (var i = 0; i < optionsList.length; i++) {
                var opt = optionsList[i];
                var exists = this.dropdownEl.find('option[value="' + opt.id + '"]').length > 0;

                // Store description in cache
                if (opt.description) {
                    this.tagDescriptions[opt.id] = opt.description;
                }

                if (!exists) {
                    var $option = $('<option>')
                        .val(opt.id)
                        .text(opt.text)
                        .prop('selected', true);
                    this.dropdownEl.append($option);
                } else {
                    this.dropdownEl
                        .find('option[value="' + opt.id + '"]')
                        .prop('selected', true)
                        .text(opt.text);
                }
            }

            this.dropdownEl.trigger('change', {silentInit: true});

            // Initialize tooltips after Select2 has rendered
            setTimeout(function() {
                self.initPopovers();
            }, 100);
        },

        togglePanel: function () {
            this.isOpen = !this.isOpen;

            if (this.isOpen) {
                this.bodyRowEl.slideDown(150);
                this.$el.find('.fa-angle-up').show();
                this.$el.find('.fa-angle-down').hide();
            } else {
                this.bodyRowEl.slideUp(150);
                this.$el.find('.fa-angle-up').hide();
                this.$el.find('.fa-angle-down').show();
            }
        },

        onApplyClick: function (e) {
            e.preventDefault();

            if (this.parent && typeof this.parent.onFilterApply === 'function') {
                this.parent.onFilterApply('taxonTags', this.getSelected());
            }
        },

        onClearClick: function (e) {
            e.preventDefault();

            this.dropdownEl.val(null).trigger('change');

            this.highlight(false);

            if (this.parent) {
                this.parent.initialSelectedTaxonTags = [];
                if (typeof this.parent.onFilterClear === 'function') {
                    this.parent.onFilterClear('taxonTags');
                }
            }
        },

        getSelected: function () {
            var vals = this.dropdownEl.val() || [];
            var encoded = [];
            for (var i = 0; i < vals.length; i++) {
                encoded.push(encodeURIComponent(vals[i]));
            }
            return encoded;
        },

        highlight: function (state) {
            if (state) {
                this.$el.find('.subtitle').addClass('filter-panel-selected');
            } else {
                this.$el.find('.subtitle').removeClass('filter-panel-selected');
            }
        }
    });
});