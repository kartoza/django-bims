define([
    'backbone',
    'ol',
    'shared',
    'underscore',
    'collections/reference_category'], function (Backbone, ol, Shared, _, ReferenceCategoryCollection) {
    return Backbone.View.extend({
        template: _.template($('#reference-category-template').html()),
        listWrapper: '',
        initialize: function (options) {
            _.bindAll(this, 'render');
            this.parent = options.parent;
            this.collection = new ReferenceCategoryCollection();
            var self = this;
            this.fetchXhr = this.collection.fetch({
                success: function () {
                    self.renderList();
                    self.parent.filtersReady['referenceCategory'] = true;
                }
                , error: function (xhr, text_status, error_thrown) {
                }
            });
        },
        render: function () {
            this.$el.html(this.template());
            this.listWrapper = this.$el.find('.reference-category');
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
                if ($.inArray(data[i].get('category'), this.parent.initialSelectedReferenceCategory) > -1) {
                    checked = 'checked';
                }
                this.listWrapper.append('<div>' +
                    '<input type="checkbox" id="reference-category-filter-'+ i +'" name="reference-category-value" value="' + data[i].get('category') + '"  ' + checked + ' >&nbsp; ' +
                        '<label class="form-check-label" for="reference-category-filter-'+ i +'">' + data[i].get('category') + '</label>' +
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
