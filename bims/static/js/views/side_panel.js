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
            Shared.Dispatcher.on('sidePanel:updateSidePanelDetail', this.updateSidePanelDetail, this);
            Shared.Dispatcher.on('sidePanel:fillSidePanelHtml', this.fillSidePanelHtml, this);
            Shared.Dispatcher.on('sidePanel:appendSidePanelContent', this.appendSidePanelContent, this);
        },
        render: function() {
            this.$el.html(this.template());
            // $('#map-container').append(this.$el);

            // Hide the side panel
            this.rightPanel = this.$el.find('.right-panel');
            this.rightPanel.css('display', 'none');

            return this;
        },
        openSidePanel: function (properties) {
            this.rightPanel.show('slide', { direction: 'right'}, 200);
            if(typeof properties !== 'undefined') {
                this.clearSidePanel();
                this.$el.find('.panel-loading').show();
                this.updateSidePanelTitle('<i class="fa fa-map-marker"></i> '+ properties['name'] +'</span>');
                if(properties.hasOwnProperty('location_type')) {
                    this.fillSidePanel(properties['location_type']);
                }
            }
        },
        updateSidePanelDetail: function(data) {
            $('.panel-icons').html('');
            this.$el.find('.panel-loading').hide();
            if(data.hasOwnProperty('biological_collection_record')) {
                var biologicalCollectionRecords = data['biological_collection_record'];
                var collections = {};
                var $panelIcons = this.$el.find('.panel-icons');
                for(var i=0; i<biologicalCollectionRecords.length; i++) {
                    var record = biologicalCollectionRecords[i];
                    var recordName = record['children_fields']['name'];
                    if(!collections.hasOwnProperty(recordName)) {
                        collections[recordName] = 1;
                        $panelIcons.append(
                            '<div class="col-lg-3 text-center">'+
                                '<img src="static/img/'+ recordName +'.svg" class="right-panel-icon">' +
                                '<p class="data-'+ recordName +' text-bold">'+collections[recordName]+'</p>'+
                                '<p>'+ recordName +' species</p>'+
                            '</div>'
                        )
                    } else {
                        collections[recordName] += 1;
                        this.$el.find('.data-'+recordName).html(collections[recordName]);
                    }
                }
            } else{
                $('#content-panel').html(JSON.stringify(data));
            }
        },
        updateSidePanelTitle: function(title) {
            var $rightPanelTitle = this.$el.find('.right-panel-title');
            $rightPanelTitle.html(title);
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
        fillSidePanelHtml: function (htmlData) {
            $('#content-panel').html(htmlData);
        },
        appendSidePanelContent: function (htmlData) {
            $('#content-panel').append(htmlData);
        },
        clearSidePanel: function () {
            $('#content-panel').html('');
            $('.panel-icons').html('');
            this.updateSidePanelTitle('');
        }
    })
});
