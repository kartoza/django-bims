define([
    'backbone',
    'shared',
    'underscore'
], function (Backbone, Shared, _) {

    return Backbone.View.extend({
        template: _.template($('#gbif-dataset-template').html()),

        initialize: function (options) {
            _.bindAll(
                this,
                'render',
                'initSelect2',
                'setInitialSelection',
                'bootstrapDatasetsByIds',
                'applyOptionsToSelect',
                'getSelected',
                'show',
                'hide',
                'clearSelection',
                'highlight'
            );

            this.parent = options.parent;
            this.dropdownEl = null;
            this.isVisible = false;

            this.parent.filtersReady['gbifDataset'] = false;
        },

        render: function () {
            this.$el.html(this.template());
            return this;
        },

        renderIntoDOM: function () {
            this.dropdownEl = this.$el.find('#gbif-dataset-search');

            this.initSelect2();

            this.setInitialSelection();

            // Mark as ready after initialization
            this.parent.filtersReady['gbifDataset'] = true;
        },

        initSelect2: function () {
            var self = this;

            this.dropdownEl.select2({
                width: '100%',
                multiple: true,
                placeholder: 'Search datasets...',
                allowClear: true,

                ajax: {
                    url: '/api/dataset-autocomplete/',
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
                            var text = data[i].name;
                            if (data[i].abbreviation) {
                                text = data[i].name + ' (' + data[i].abbreviation + ')';
                            }
                            results.push({
                                id: data[i].id,
                                text: text
                            });
                        }
                        return { results: results };
                    },
                    cache: true
                },

                closeOnSelect: false,

                templateSelection: function (item) {
                    return item.text || item.id;
                },

                templateResult: function (item) {
                    if (item.loading) {
                        return item.text;
                    }
                    return item.text || item.id;
                }
            });
        },

        setInitialSelection: function () {
            var self = this;
            var initial = this.parent.initialSelectedGbifDatasets || [];
            if (!initial.length) {
                this.highlight(false);
                return;
            }

            var knownOptions = [];
            var unknownIds = [];

            for (var i = 0; i < initial.length; i++) {
                var datasetItem = initial[i];

                if (typeof datasetItem === 'object' && datasetItem !== null) {
                    if (datasetItem.id !== undefined) {
                        knownOptions.push({
                            id: datasetItem.id,
                            text: datasetItem.name || ('' + datasetItem.id)
                        });
                    }
                } else {
                    unknownIds.push(datasetItem);
                }
            }

            if (knownOptions.length) {
                this.applyOptionsToSelect(knownOptions);
            }

            if (unknownIds.length) {
                this.bootstrapDatasetsByIds(unknownIds).done(function (resolvedOptions) {
                    self.applyOptionsToSelect(resolvedOptions);
                    self.highlight(self.getSelected().length > 0);
                }).fail(function () {
                    self.highlight(self.getSelected().length > 0);
                });
            } else {
                this.highlight(this.getSelected().length > 0);
            }
        },

        /**
         * Hit /api/dataset-autocomplete/?ids=1,2,3
         * and convert to [{id:1,text:"Dataset Name"}, ...]
         */
        bootstrapDatasetsByIds: function (idsArray) {
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
                url: '/api/dataset-autocomplete/',
                dataType: 'json',
                data: {
                    ids: uniqueIds.join(',')
                },
                success: function (data) {
                    var opts = [];
                    for (var j = 0; j < data.length; j++) {
                        var text = data[j].name;
                        if (data[j].abbreviation) {
                            text = data[j].name + ' (' + data[j].abbreviation + ')';
                        }
                        opts.push({
                            id: data[j].id,
                            text: text
                        });
                    }
                    dfd.resolve(opts);
                },
                error: function () {
                    console.warn('Failed to load some datasets');
                    dfd.resolve([]);
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
                        .text(opt.text);
                }
            }

            this.dropdownEl.trigger('change', {silentInit: true});
        },

        getSelected: function () {
            if (!this.dropdownEl) {
                return [];
            }
            var vals = this.dropdownEl.val() || [];
            var encoded = [];
            for (var i = 0; i < vals.length; i++) {
                encoded.push(encodeURIComponent(vals[i]));
            }
            return encoded;
        },

        show: function () {
            this.$el.find('.gbif-dataset-wrapper').show();
            this.isVisible = true;
        },

        hide: function () {
            this.$el.find('.gbif-dataset-wrapper').hide();
            this.isVisible = false;
        },

        clearSelection: function () {
            if (this.dropdownEl) {
                this.dropdownEl.val(null).trigger('change');
            }
            this.highlight(false);
            if (this.parent) {
                this.parent.initialSelectedGbifDatasets = [];
            }
        },

        highlight: function (state) {
            // No subtitle in this view, so highlight the label instead
            if (state) {
                this.$el.find('label').addClass('filter-panel-selected');
            } else {
                this.$el.find('label').removeClass('filter-panel-selected');
            }
        }
    });
});
