define([
    'backbone',
    'ol',
    'shared',
    'underscore',
    'collections/source_collection'], function (Backbone, ol, Shared, _, SourceCollection) {
    return Backbone.View.extend({
        template: _.template($('#source-collection-template').html()),
        listWrapper: '',
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
                label = label.charAt(0).toUpperCase() + label.slice(1);
                if ($.inArray(data[i].get('source_collection'), this.parent.initialSelectedSourceCollection) > -1) {
                    checked = 'checked';
                }
                this.listWrapper.append('<div>' +
                    '<input type="checkbox" id="source-collection-list-'+i+'" name="source-collection-value" value="' + data[i].get('source_collection') + '"  ' + checked + ' >&nbsp;' +
                    '<label for="source-collection-list-'+i+'" >'+ label + '</label>' +
                    '</div>');
            }
        },
        getSelected: function () {
            var selected = [];
            this.$el.find('input:checked').each(function () {
                selected.push($(this).val())
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
