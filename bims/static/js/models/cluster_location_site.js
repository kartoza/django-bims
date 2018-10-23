define(['backbone'], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            id: 0,
            name: '',
            coordinates: ''
        },
        getId: function () {
            return parseInt(this.get('id'));
        },
        getCoordinates: function () {
            if (!this.get('coordinates')) {
                return [0, 0];
            }

            var coordinatesArray = this.get('coordinates').split(',');
            var lon = parseFloat(coordinatesArray[0]);
            var lat = parseFloat(coordinatesArray[1]);
            return [lon, lat];
        },
        destroy: function () {
            this.unbind();
            delete this;
        }
    })
});
