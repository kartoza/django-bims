define(['backbone'], function (Backbone) {
    describe("Biological", function() {
        it("should expose an Attribute", function() {
            var biological = new Backbone.Model({
                title: "Hollywood"
            });
            expect(biological.get('title')).toEqual("Hollywood");
        });
    });
});
