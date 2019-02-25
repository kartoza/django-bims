define([
    'backbone',
    'models/biological',
    'views/location_site'
], function (Backbone, Biological, LocationSiteView) {

    describe("Biological Model", function() {
        it("should expose an Attribute", function() {
            let biological = new Biological({
                title: "species_name"
            });
            expect(biological.get('title')).toEqual("species_name");
        });
    });

});
