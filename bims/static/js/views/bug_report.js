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
        template: _.template($('#bug-report').html()),
        summaryTextDiv: null,
        descriptionTextDiv: null,
        submitButton: null,
        submitButtonActive: false,
        panel: null,
        loadingPanel: null,
        panelDisplayed: true,
        loading: false,
        successFeedbackDiv: null,
        errorFeedbackDiv: null,
        moved: false,
        ticketLinkDiv: null,
        events: {
            'click .bug-report-button': 'toggleReportPanel',
            'click .close-brp-panel': 'toggleReportPanel',
            'keyup #report-summary': 'textAreaOnChanged',
            'keyup #report-description': 'textAreaOnChanged',
            'click #submit-report-button': 'submitReport'
        },
        initialize: function () {
            Shared.Dispatcher.on('bugReport:moveLeft', this.moveLeft, this);
            Shared.Dispatcher.on('bugReport:moveRight', this.moveRight, this)
        },
        render: function () {
            this.$el.html(this.template());
            this.summaryTextDiv = this.$el.find('#report-summary');
            this.descriptionTextDiv = this.$el.find('#report-description');
            this.submitButton = this.$el.find('#submit-report-button');
            this.loadingPanel = this.$el.find('.brp-loading-panel');
            this.panel = this.$el.find('.bug-report-panel');
            this.successFeedbackDiv = this.$el.find('.success-feedback');
            this.errorFeedbackDiv = this.$el.find('.error-feedback');
            this.container = $(this.$el.find('.bug-report-wrapper').get(0));
            this.ticketLinkDiv = this.$el.find('#ticket-link');
            if (!is_logged_in) {
                this.summaryTextDiv.attr('disabled', true);
                this.descriptionTextDiv.attr('disabled', true);
                this.$el.find('#report-type').attr('disabled', true);
                this.$el.find('.warning-feedback').show();
            }
            return this;
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
        textAreaOnChanged: function () {
            if (this.loading) {
                return false;
            }
            if (this.summaryTextDiv.val().length >= 5 && this.descriptionTextDiv.val().length > 0) {
                if (!this.submitButtonActive) {
                    this.submitButtonActive = true;
                    this.submitButton.attr("disabled", false);
                }
            } else {
                this.submitButtonActive = false;
                this.submitButton.attr("disabled", true);
            }
        },
        toggleReportPanel: function () {
            this.panel.toggle();
            this.successFeedbackDiv.hide();
            this.errorFeedbackDiv.hide();
            this.ticketLinkDiv.html('');
        },
        submitReport: function () {
            var self = this;
            if (this.loading) {
                return false;
            }
            this.submitButton.attr("disabled", true);
            this.loading = true;
            let summaryWrapper = this.$el.find('.brp-summary');
            let descriptionWrapper = this.$el.find('.brp-description');
            let reportTypeDiv = this.$el.find('#report-type');
            summaryWrapper.toggle();
            descriptionWrapper.toggle();
            this.loadingPanel.toggle();
            let browser = getBrowser();
            let additionalInformation = {
                'browser': browser['browser'],
                'device': browser['device'],
                'referrer': window.location.href,
                'screen resolution': browser['screen_resolution']
            };

            let labels = [];
            labels.push(reportTypeDiv.val());
            labels.push('user-feedback');
            reportTypeDiv.attr('disabled', true);

            let postData = {
                'summary': this.summaryTextDiv.val(),
                'description': this.descriptionTextDiv.val(),
                'labels': labels.join(','),
                'json_additional_information': JSON.stringify(additionalInformation)
            };

            $.ajax({
                url: reportUrl,
                type: 'POST',
                data: postData,
                dataType: 'text',
                success: function (data) {
                    let ticketNumber = JSON.parse(data)['ticket_number'];
                    self.ticketLinkDiv.html(`<a href="http://github.com/${githubRepo}/issues/${ticketNumber}" target="_blank">#${ticketNumber}</a>`);
                    self.successFeedbackDiv.show();
                },
                error: function () {
                    self.errorFeedbackDiv.show();
                },
                complete: function(data) {
                    if (self.loading) {
                        self.loading = false;
                        self.summaryTextDiv.val('').blur();
                        self.descriptionTextDiv.val('').blur();
                        summaryWrapper.toggle();
                        descriptionWrapper.toggle();
                        self.loadingPanel.toggle();
                        reportTypeDiv.attr('disabled', false);
                    }
                },
            });
        }
    })
});