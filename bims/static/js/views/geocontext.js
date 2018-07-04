define(['backbone', 'underscore', 'shared', 'ol'], function (Backbone, _, Shared, ol) {
    return Backbone.View.extend({
        geocontextUrl: _.template(
            "https://geocontext.kartoza.com/geocontext/value/list/<%= latitude %>/<%= longitude %>/?with-geometry=False"),
        loadSuccess: function () {
            $('#geocontext-information-container img').hide();
            $('#geocontext-information-container .content').show();
        },
        loadGeocontext: function (latitude, longitude) {
            var self = this;
            $('#geocontext-information-container').show();
            $('#geocontext-information-container img').show();
            $('#geocontext-information-container .content').hide();
            $('#geocontext-information-container .content').html("");

            if (this.geocontextXhr) {
                this.geocontextXhr.abort();
            }
            this.geocontextXhr = $.get({
                url: this.geocontextUrl({
                    'latitude': latitude,
                    'longitude': longitude
                }),
                dataType: 'json',
                success: function (data) {
                    self.loadSuccess();
                    $.each(data, function (index, value) {
                        $('#geocontext-information-container .content').append(
                            "<tr><td>" + value['name'] + "</td><td>" + value['value'] + "</td></tr>"
                        )
                    });
                },
                error: function (req, err) {
                    self.loadSuccess();
                }
            });
        }
    })
});