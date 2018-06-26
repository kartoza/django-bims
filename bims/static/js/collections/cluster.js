define(['backbone', 'models/cluster', 'views/cluster'], function (Backbone, ClusterModel, ClusterView) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: "/api/cluster/",
        cache: {},
        url: "",
        viewCollection: [],
        updateUrl: function (administrative) {
            this.administrative = administrative;
            this.url = this.clusterAPI + administrative
        },
        getCache: function () {
            return this.cache[this.administrative];
        },
        applyCache: function () {
            this.models = this.cache[this.administrative];
            this.renderCollection();
        },
        renderCollection: function () {
            var self = this;
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];
            this.cache[this.administrative] = [];
            $.each(this.models, function (index, model) {
                self.cache[self.administrative].push(model);
                self.viewCollection.push(new ClusterView({
                    model: model
                }));
            });
        }
    })
});
