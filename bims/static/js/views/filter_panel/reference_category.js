define([
    'backbone', 
    'ol',
    'shared', 
    'underscore', 
    'collections/reference_category'], function (Backbone, ol, Shared, _, ReferenceCategoryCollection) {
    return Backbone.View.extend({
        template: _.template($('#reference-category-template').html()),
        listWrapper: '',
        initialize: function () {
            _.bindAll(this, 'render');
            this.collection = new ReferenceCategoryCollection();
            var self = this;
            this.fetchXhr = this.collection.fetch({
                success: function () {
                    self.renderList();
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
            for(var i=0; i<data.length; i++) {
                this.listWrapper.append('<div>' +
                    '<input type="checkbox" name="reference-category-value" value="">&nbsp;'+data[i].get('category')+
                    '</div>');
            }
        }
    })
});
