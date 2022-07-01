define([
    'backbone',
    'ol',
    'shared',
    'underscore',
    'collections/source_collection'], function (Backbone, ol, Shared, _, SourceCollection) {
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

                // If source_collection named fbis is first => set the checkbox disabled
                if (data[i].get('source_collection') === 'fbis' && i === 0) {
                    isFBIS = true;
                }

                let dataSourceCaption = '';
                if (this.dataSourceCaptions.hasOwnProperty(label.toLowerCase()) && isFBIS) {
                    dataSourceCaption = '<div class="data-source-desc" style="display: none"><small class="text-muted">'+ this.dataSourceCaptions[label.toLowerCase()] +'</small></div>';
                }
                this.listWrapper.append('<div style="padding-bottom: 10px;">' +
                    '<input type="checkbox" id="source-collection-list-'+i+'" name="source-collection-value" value="' + data[i].get('source_collection') + '"  ' + checked + ' >&nbsp;' +
                    '<label for="source-collection-list-'+i+'" style="margin-bottom: 0 !important;">'+ label.replace('_', ' ').toUpperCase() + '</label>' +
                    (this.dataSourceCaptions.hasOwnProperty(label.toLowerCase()) && isFBIS ? '<span>&nbsp;<i class="fa fa-info-circle layer-source data-source" aria-hidden="true"></i></span>' : '') +
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
