$(function () {
    let $wrapper = $('#bug-report-wrapper');

    let summaryTextDiv = $wrapper.find('#report-summary');
    let descriptionTextDiv = $wrapper.find('#report-description');
    let submitButton = $wrapper.find('#submit-report-button');
    let loadingPanel = $wrapper.find('.brp-loading-panel');
    let panel = $wrapper.find('.bug-report-panel');
    let successFeedbackDiv = $wrapper.find('.success-feedback');
    let errorFeedbackDiv = $wrapper.find('.error-feedback');
    let container = $($wrapper.find('.bug-report-wrapper').get(0));
    let ticketLinkDiv = $wrapper.find('#ticket-link');
    let bugReportButton = $wrapper.find('.bug-report-button');
    let closePanel = $wrapper.find('.close-brp-panel');
    let submitButtonActive = false;
    let loading = false;

    if (!is_logged_in) {
        summaryTextDiv.attr('disabled', true);
        descriptionTextDiv.attr('disabled', true);
        $wrapper.find('#report-type').attr('disabled', true);
        $wrapper.find('.warning-feedback').show();
    }

    // Bind events
    bugReportButton.click(toggleReportPanel);
    closePanel.click(toggleReportPanel);
    summaryTextDiv.keyup(textAreaOnChanged);
    descriptionTextDiv.keyup(textAreaOnChanged);
    submitButton.click(submitReport);

    function toggleReportPanel() {
        panel.toggle();
        successFeedbackDiv.hide();
        errorFeedbackDiv.hide();
        ticketLinkDiv.html('');
    }

    function textAreaOnChanged() {
        if (loading) {
            return false;
        }
        if (summaryTextDiv.val().length >= 5 && descriptionTextDiv.val().length > 0) {
            if (!submitButtonActive) {
                submitButtonActive = true;
                submitButton.attr("disabled", false);
            }
        } else {
            submitButtonActive = false;
            submitButton.attr("disabled", true);
        }
    }
    
    function submitReport() {
        if (loading) {
            return false;
        }
        submitButton.attr("disabled", true);
        loading = true;
        let summaryWrapper = $wrapper.find('.brp-summary');
        let descriptionWrapper = $wrapper.find('.brp-description');
        let reportTypeDiv = $wrapper.find('#report-type');
        summaryWrapper.toggle();
        descriptionWrapper.toggle();
        loadingPanel.toggle();
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
            'summary': summaryTextDiv.val(),
            'description': descriptionTextDiv.val(),
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
                ticketLinkDiv.html(`<a href="http://github.com/${githubRepo}/issues/${ticketNumber}" target="_blank">#${ticketNumber}</a>`);
                successFeedbackDiv.show();
            },
            error: function () {
                errorFeedbackDiv.show();
            },
            complete: function(data) {
                if (loading) {
                    loading = false;
                    summaryTextDiv.val('').blur();
                    descriptionTextDiv.val('').blur();
                    summaryWrapper.toggle();
                    descriptionWrapper.toggle();
                    loadingPanel.toggle();
                    reportTypeDiv.attr('disabled', false);
                }
            },
        });
    }
    
});