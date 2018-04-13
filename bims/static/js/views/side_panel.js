define(['shared', 'backbone', 'underscore', 'jqueryUi'], function(Shared, Backbone, _) {
    return Backbone.View.extend({
        template: _.template($('#side-panel-template').html()),
        className: 'panel-wrapper',
        rightPanel: null,
        events: {
            'click .close-panel': 'closeSidePanel'
        },
        initialize: function () {
            // Events
            Shared.Dispatcher.on('sidePanel:openSidePanel', this.openSidePanel, this);
            Shared.Dispatcher.on('sidePanel:closeSidePanel', this.closeSidePanel, this);
        },
        render: function() {
            this.$el.html(this.template());
            $('#map-container').append(this.$el);

            // Hide the side panel
            this.rightPanel = this.$el.find('.right-panel');
            this.rightPanel.css('display', 'none');

            return this;
        },
        openSidePanel: function (properties) {
            this.rightPanel.show('slide', { direction: 'right'}, 200);
            if(properties) {
                this.clearSidePanel();
                this.setSiteName(properties['name']);
                if(properties.hasOwnProperty('location_type')) {
                    this.fillSidePanel(properties['location_type']);
                }
                if(properties.hasOwnProperty('fish_collection_records')) {
                    this.setTotalFish(properties['fish_collection_records'].length);
                }
            }
        },
        setSiteName: function(name) {
            var $siteName = this.$el.find('.site-name');
            $siteName.html(name);
        },
        setTotalFish: function(total) {
            var $dataFish = this.$el.find('.data-fish');
            $dataFish.html(total);
        },
        closeSidePanel: function (e) {
            var self = this;
            this.rightPanel.hide('slide', { direction: 'right'}, 200, function () {
                self.clearSidePanel();
            });
        },
        fillSidePanel: function (contents) {
            for (var key in contents) {
                if (contents.hasOwnProperty(key)) {
                    $('#content-panel').append('<p>'+ key.charAt(0).toUpperCase() + key.substring(1) +' : '+ contents[key] +'</p>');
                }
            }
        },
        clearSidePanel: function () {
            $('#content-panel').html('');
        }
    })
});
