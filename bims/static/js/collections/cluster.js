define(['backbone', 'models/cluster', 'views/cluster'], function (Backbone, ClusterModel, ClusterView) {
    return Backbone.Collection.extend({
        model: ClusterModel,
        clusterAPI: "/api/cluster/",
        url: "",
        viewCollection: [],
        updateUrl: function (administrative) {
            this.administrative = administrative;
            this.url = this.clusterAPI + administrative
        },
        renderCollection: function () {
            var self = this;
            $.each(this.viewCollection, function (index, view) {
                view.destroy();
            });
            this.viewCollection = [];
            $.each(this.models, function (index, model) {
                self.viewCollection.push(new ClusterView({
                    model: model
                }));
            });
        }
    })
});
