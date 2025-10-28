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
                'onClearClick'
            );

            this.parent = options.parent;
            this.dropdownEl = null;
            this.bodyRowEl = null;
            this.isOpen = false;

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
                            results.push({
                                id: data[i].id,
                                text: data[i].name
                            });
                        }
                        return { results: results };
                    },
                    cache: true
                },

                closeOnSelect: false,

                templateSelection: function (item) {
                    return item.text || item.name || item.id;
                },

                templateResult: function (item) {
                    if (item.loading) {
                        return item.text;
                    }
                    return item.text || item.name || item.id;
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
         * and convert to [{id:1,text:"Terrestrial"}, ...]
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
                        opts.push({
                            id: data[j].id,
                            text: data[j].name
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
            for (var i = 0; i < optionsList.length; i++) {
                var opt = optionsList[i];
                var exists = this.dropdownEl.find('option[value="' + opt.id + '"]').length > 0;

                if (!exists) {
                    this.dropdownEl.append(
                        $('<option>')
                            .val(opt.id)
                            .text(opt.text)
                            .prop('selected', true)
                    );
                } else {
                    this.dropdownEl
                        .find('option[value="' + opt.id + '"]')
                        .prop('selected', true)
                        .text(opt.text)
                }
            }

            this.dropdownEl.trigger('change', {silentInit: true});
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