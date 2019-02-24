function downloadCSV(url, downloadButton) {
    let self = this;
    self.downloadCSVXhr = $.get({
        url: url,
        dataType: 'json',
        success: function (data) {
            if (data['status'] !== "success") {
                if (data['status'] === "failed") {
                    if (self.downloadCSVXhr) {
                        self.downloadCSVXhr.abort();
                    }
                    downloadButton.html('Download as CSV');
                    downloadButton.prop("disabled", false);
                } else {
                    setTimeout(
                        function () {
                            downloadCSV(url, downloadButton);
                        }, 5000);
                }
            } else {
                var is_safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
                if (is_safari) {
                    var a = window.document.createElement('a');
                    a.href = '/uploaded/csv_processed/' + data['message'];
                    a.download = data['message'];
                    a.click();
                } else {
                    location.replace('/uploaded/csv_processed/' + data['message']);
                }

                downloadButton.html('Download as CSV');
                downloadButton.prop("disabled", false);
            }
        },
        error: function (req, err) {
        }
    });
}