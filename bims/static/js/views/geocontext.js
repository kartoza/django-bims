define(['backbone', 'underscore', 'shared', 'ol', 'jquery'], function (Backbone, _, Shared, ol, $) {
    return Backbone.View.extend({
        geocontextUrl: _.template(
            "<%= geocontextUrl %>/api/v2/query?registry=collection&key=<%= geocontextCollectionKey %>&x=<%= longitude %>&y=<%= latitude %>"),
        loadSuccess: function () {
            $('#geocontext-information-container img').hide();
            $('#geocontext-information-container .content').show();
        },
        loadGeocontext: function (latitude, longitude) {
            var self = this;
            $('#geocontext-information-container').show();
            $('#geocontext-information-container img').show();
            $('#geocontext-information-container .content').hide();
            $('#geocontext-information-container .content').empty();

            if (this.geocontextXhr) {
                this.geocontextXhr.abort();
            }
            this.geocontextXhr = $.get({
                url: this.geocontextUrl({
                    'geocontextUrl': geocontextUrl,
                    'latitude': latitude,
                    'longitude': longitude,
                    'geocontextCollectionKey': geocontextCollectionKey,
                }),
                dataType: 'json',
                success: function (data) {
                    self.loadSuccess();
                    var geocontext_content = "";
                    // Set title to collection name
                    geocontext_content = geocontext_content.concat(
                            "<div>Collection: " + data['name'] + "</div>\n");
                    // Iterate data for all context groups
                    $.each(data["groups"], function (index, group_value) {
                        geocontext_content = geocontext_content.concat(
                            "<div> Group: " + group_value['name'] + "</div>\n");
                        geocontext_content = geocontext_content.concat(
                            "<table >\n");
                        $.each(group_value["services"], function (index_csr, csr) {
                            geocontext_content = geocontext_content.concat(
                                "<tr>" +
                                "<td>" + csr['name'] + "</td>" +
                                "<td>" + csr['value'] + "</td>" +
                                "</tr>"
                            );
                        });
                        geocontext_content = geocontext_content.concat("</table>");
                    });
                    // Append content to the div
                    $('#geocontext-information-container .content').append(geocontext_content);
                },
                error: function (req, err) {
                    self.loadSuccess();
                }
            });
        },
        loadGeocontextByID: function (locationSiteID) {
            var self = this;
            $('#geocontext-information-container').show();
            $('#geocontext-information-container img').show();
            $('#geocontext-information-container .content').hide();
            $('#geocontext-information-container .content').empty();

            // URL building
            var url = '';

            if (this.geocontextXhr) {
                this.geocontextXhr.abort();
            }
            this.geocontextXhr = $.get({
                url: url,
                dataType: 'json',
                success: function (data) {
                    data = data['location_context_document_json'];
                    if (!data){
                        self.loadSuccess();
                        return;
                    }
                    self.loadSuccess();
                    var geocontext_content = "";
                    // Set title to collection name
                    geocontext_content = geocontext_content.concat(
                            "<div>Collection: " + data['name'] + "</div>\n");
                    // Iterate data for all context groups
                    $.each(data["groups"], function (index, group_value) {
                        geocontext_content = geocontext_content.concat(
                            "<div> Group: " + group_value['name'] + "</div>\n");
                        geocontext_content = geocontext_content.concat(
                            "<table >\n");
                        $.each(group_value["services"], function (index_csr, csr) {
                            geocontext_content = geocontext_content.concat(
                                "<tr>" +
                                "<td>" + csr['name'] + "</td>" +
                                "<td>" + csr['value'] + "</td>" +
                                "</tr>"
                            );
                        });
                        geocontext_content = geocontext_content.concat("</table>");
                    });
                    // Append content to the div
                    $('#geocontext-information-container .content').append(geocontext_content);
                },
                error: function (req, err) {
                    self.loadSuccess();
                }
            });
        }
    })
});