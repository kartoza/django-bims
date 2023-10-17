define([
    'backbone',
    'underscore',
    'shared',
    'jquery',
    'utils/detect-browser'
], function (
    Backbone,
    _,
    Shared,
    $,
    DetectBrowser
) {
    return Backbone.View.extend({
        template: _.template($('#wetland-mapping-feedback').html()),
        currentLocation: null,
        loading: false,
        submitButtonActive: false,
        events: {
            'click .wetland-mapping-button': 'toggleFeedbackPanel',
            'click .close-wetland-mapping-panel': 'toggleFeedbackPanel',
            'click #submit-feedback-button': 'submitFeedback',
            'keyup #wetland-feedback-issue': 'textAreaOnChanged',
            'keyup #wetland-feedback-desc': 'textAreaOnChanged',
        },
        initialize: function () {
            Shared.Dispatcher.on('wetlandFeedback:locationUpdated', this.locationUpdated, this);
            Shared.Dispatcher.on('bugReport:moveLeft', this.moveLeft, this);
            Shared.Dispatcher.on('bugReport:moveRight', this.moveRight, this)
        },
        moveLeft: function () {
            let self = this;
            if (!Shared.SidePanelOpen) {
                return;
            }
            if (this.moved) {
                return;
            }
            let width = $('.panel-wrapper').width() + 5;
            self.moved = true;
            this.container.animate({
                "right": "+=" + width + 'px'
            }, 100, function () {
                // Animation complete
            })
        },
        moveRight: function () {
            let self = this;
            if (!self.moved) {
                return;
            }
            let width = $('.panel-wrapper').width() + 5;
            self.moved = false;
            this.container.animate({
                "right": "-=" + width + "px"
            }, 100, function () {
                // Animation complete
            })
        },
        render: function () {
            this.$el.html(this.template());
            this.issueTextDiv = this.$el.find('#wetland-feedback-issue');
            this.descriptionTextDiv = this.$el.find('#wetland-feedback-desc');
            this.issueTypeDiv = this.$el.find('#wetland-feedback-type');
            this.loadingPanel = this.$el.find('.brp-loading-panel');
            this.allWetlandForm = this.$el.find('.wetland-form');

            this.panel = this.$el.find('.wetland-mapping-feedback-panel');
            this.container = $(this.$el.find('#wetland-map-feedback').get(0));
            this.successFeedback = this.$el.find('.success-feedback');
            this.warningFeedback = this.$el.find('.warning-feedback');
            this.submitButton = this.$el.find('#submit-feedback-button');
            return this;
        },
        textAreaOnChanged: function () {
            if (this.loading) {
                return false;
            }
            if (this.issueTextDiv.val().length >= 0 && this.descriptionTextDiv.val().length > 0 && this.currentLocation) {
                if (!this.submitButtonActive) {
                    this.submitButtonActive = true;
                    this.submitButton.attr("disabled", false);
                }
            } else {
                this.submitButtonActive = false;
                this.submitButton.attr("disabled", true);
            }
        },
        locationUpdated: function (coordinates) {
            this.currentLocation = coordinates;
            this.successFeedback.html(`Lon : ${coordinates[0]} <br/> Lat : ${coordinates[1]}`);
            this.successFeedback.show();
            this.warningFeedback.hide();
            this.textAreaOnChanged();
        },
        submitFeedback: function () {
            let self = this;
            this.loading = true;
            let postData = {
                'issue': this.issueTextDiv.val(),
                'issue_type': this.issueTypeDiv.val(),
                'description': this.descriptionTextDiv.val(),
                'location': this.currentLocation.join(',')
            };

            self.successFeedback.hide();
            self.warningFeedback.show();
            self.warningFeedback.html('Submitting...')
            self.submitButton.attr("disabled", true);
            self.allWetlandForm.toggle();
            self.loadingPanel.toggle();

            $.ajax({
                url: wetlandFeedbackUrl,
                headers: {"X-CSRFToken": csrfmiddlewaretoken},
                type: 'POST',
                data: postData,
                dataType: 'text',
                success: function (data) {
                    self.warningFeedback.html('Select location on the map.');
                    self.successFeedback.show();
                    self.warningFeedback.hide();
                },
                error: function () {
                    self.loading = false;
                    self.loadingPanel.toggle();
                    self.allWetlandForm.toggle();
                    self.warningFeedback.html('An error occurred while submitting the feedback. Please try again later.')
                    self.warningFeedback.show();
                    self.submitButtonActive = false;
                    Shared.Dispatcher.trigger('wetlandFeedback:togglePanel');
                    Shared.Dispatcher.trigger('wetlandFeedback:togglePanel');
                },
                complete: function(data) {
                    if (self.loading) {
                        self.loading = false;
                        self.issueTextDiv.val('').blur();
                        self.descriptionTextDiv.val('').blur();
                        self.submitButton.attr("disabled", false);
                        self.allWetlandForm.toggle();
                        self.loadingPanel.toggle();
                        self.panel.toggle();
                        Shared.Dispatcher.trigger('wetlandFeedback:togglePanel');
                        alert('The feedback has been successfully submitted.');
                    }
                },
            });
        },
        toggleFeedbackPanel: function () {
            if (this.loading) {
                return;
            }
            this.currentLocation = null;
            this.successFeedback.hide();
            this.warningFeedback.show();
            this.panel.toggle();
            Shared.Dispatcher.trigger('wetlandFeedback:togglePanel');
        },
    })
});
