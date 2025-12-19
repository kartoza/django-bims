define([
    'backbone',
    'shared',
    'underscore',
    'collections/source_collection'], function (Backbone, Shared, _, SourceCollection) {
    return Backbone.View.extend({
        template: _.template($('#source-collection-template').html()),
        events: {
            'click .data-source': 'toggleDataSourceDescription'
        },
        listWrapper: '',
        dataSourceCaptions: {
            "fbis": "Data not available via GBIF that have been sourced and collated from reputable " +
                "databases, peer-reviewed scientific articles, published reports, theses and other unpublished data sources.",
            "gbif": "Freshwater species occurrence data available for South Africa" +
                " that are currently available via the Global Biodiversity Information " +
                "Facility (GBIF). GBIF includes periodically-updated data from the South" +
                " African Institute for Aquatic Biodiversity (SAIAB), as well as 'Research Grade' " +
                "iNaturalist data (i.e. records from non-captive individuals, with a picture, locality " +
                "and date, and with two or more IDs in agreement at species level). " +
                "Invertebrate data includes both aquatic and aerial stages.",
            "virtual_museum": "Freshwater species occurrence data for South Africa that are currently available at Virtual Museum (VM) " +
              "(<a href='https://vmus.adu.org.za/' target='_blank'>https://vmus.adu.org.za/</a>). VM is a platform for citizen scientists to contribute to biodiversity data and is managed by " +
              "The Biodiversity and Development Institute (<a href='http://thebdi.org/' target='_blank'>http://thebdi.org/</a>) and The FitzPatrick Institute of African Ornithology " +
              "(<a href='http://www.fitzpatrick.uct.ac.za/' target='_blank'>http://www.fitzpatrick.uct.ac.za/</a>)."
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
            let isFBIS = false;
            if (data.length === 0) {
                this.$el.hide();
                return false;
            }
            let dataSources = data[0].attributes;
            for (const [label, desc] of Object.entries(dataSources)) {
                var checked = '';
                if (label === null) {
                    continue;
                }
                let updatedLabel = label.charAt(0).toUpperCase() + label.slice(1);
                if ($.inArray(label, this.parent.initialSelectedSourceCollection) > -1) {
                    checked = 'checked';
                }

                if (Object.keys(dataSources).hasOwnProperty('fbis')) {
                    isFBIS = true;
                }

                let dataSourceCaption = '';
                dataSourceCaption = '<div class="data-source-desc" style="display: none"><small class="text-muted">'+ desc +'</small></div>';
                this.listWrapper.append('<div style="padding-bottom: 10px;">' +
                    '<input type="checkbox" id="source-collection-list-'+label+'" name="source-collection-value" value="' + label + '"  ' + checked + ' >&nbsp;' +
                    '<label for="source-collection-list-'+label+'" style="margin-bottom: 0 !important;">'+ updatedLabel.replace('_', ' ').toUpperCase() + '</label>' +
                    (desc ? '<span>&nbsp;<i class="fa fa-info-circle layer-source data-source" aria-hidden="true"></i></span>' : '') +
                    dataSourceCaption +
                    '</div>');

            }
        },
        toggleDataSourceDescription: function (e) {
            const $dataSourceDesc = $(e.target).parent().parent().find('.data-source-desc');
            $dataSourceDesc.toggle();
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
