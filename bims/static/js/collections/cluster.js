define(['shared', 'backbone', 'models/cluster', 'views/location_site', 'views/cluster'], function (Shared, Backbone, ClusterModel, ClusterView) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: "/api/cluster/",
        cache: {},
        url: "",
        viewCollection: [],
        initialize: function () {
            Shared.Dispatcher.on('cluster:updateAdministrative', this.updateUrl, this);
        },
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
