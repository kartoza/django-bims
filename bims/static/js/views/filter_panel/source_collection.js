define([
    'backbone',
    'ol',
    'shared',
    'underscore',
    'collections/source_collection'], function (Backbone, ol, Shared, _, SourceCollection) {
    return Backbone.View.extend({
        template: _.template($('#source-collection-template').html()),
        listWrapper: '',
        dataSourceCaptions: {
            "fbis": "Data not available via GBIF that have been sourced and collated from reputable " +
                "databases, peer-reviewed scientific articles, published reports, theses and other unpublished data sources.",
            "gbif_fbis": "Freshwater species occurrence data available for South Africa" +
                " that are currently available via the Global Biodiversity Information " +
                "Facility (GBIF). GBIF includes periodically-updated data from the South" +
                " African Institute for Aquatic Biodiversity (SAIAB), as well as 'Research Grade' " +
                "iNaturalist data (i.e. records from non-captive individuals, with a picture, locality " +
                "and date, and with two or more IDs in agreement at species level). " +
                "Invertebrate data includes both aquatic and aerial stages."
        },
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.collection = new SourceCollection();
            var self = this;
            this.fetchXhr = this.collection.fetch({
                success: function () {
                    self.renderList();
                    self.parent.filtersReady['sourceCollection'] = true;
                }
                , error: function (xhr, text_status, error_thrown) {
                }
            });
        },
        render: function () {
            this.$el.html(this.template());
            this.listWrapper = this.$el.find('.data-source-list');
            return this;
        },
        renderList: function () {
            var data = this.collection.models;
            if (data.length === 0) {
                this.$el.hide();
                return false;
            }
            for (var i = 0; i < data.length; i++) {
                var checked = '';
                var label = data[i].get('source_collection');
                if (label === null) {
                    continue;
                }
                label = label.charAt(0).toUpperCase() + label.slice(1);
                if ($.inArray(data[i].get('source_collection'), this.parent.initialSelectedSourceCollection) > -1) {
                    checked = 'checked';
                }

                // If source_collection called fbis is first, then set it disabled
                if (data[i].get('source_collection') === 'fbis' && i === 0) {
                    checked += ' disabled';
                }

                let dataSourceCaption = '';
                if (this.dataSourceCaptions.hasOwnProperty(label.toLowerCase())) {
                    dataSourceCaption = '<br/><small class="text-muted">'+ this.dataSourceCaptions[label.toLowerCase()] +'</small>';
                }
                this.listWrapper.append('<div style="padding-bottom: 10px;">' +
                    '<input type="checkbox" id="source-collection-list-'+i+'" name="source-collection-value" value="' + data[i].get('source_collection') + '"  ' + checked + ' >&nbsp;' +
                    '<label for="source-collection-list-'+i+'" style="margin-bottom: 0 !important;">'+ label.toUpperCase() + '</label>' +
                    dataSourceCaption +
                    '</div>');
            }
        },
        updateChecked: function () {
            let self = this;
            $.each(this.parent.initialSelectedSourceCollection, function (index, sourceCollection) {
                self.listWrapper.find(':input[value="'+sourceCollection+'"]').prop('checked', true);
            });
        },
        getSelected: function () {
            var selected = [];
            this.$el.find('input:checked').each(function () {
                selected.push(encodeURIComponent($(this).val()));
            });
            return selected;
        },
        highlight: function (state) {
            if (state) {
                this.$el.find('.subtitle').addClass('filter-panel-selected');
            } else {
                this.$el.find('.subtitle').removeClass('filter-panel-selected');
            }
        }
    })
});
