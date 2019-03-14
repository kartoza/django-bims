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

function downloadCSV2(csv, filename) {
    var csvFile;
    var downloadLink;

    // CSV file
    csvFile = new Blob([csv], {type: "text/csv"});

    // Download link
    downloadLink = document.createElement("a");

    // File name
    downloadLink.download = filename;

    // Create a link to the file
    downloadLink.href = window.URL.createObjectURL(csvFile);

    // Hide download link
    downloadLink.style.display = "none";

    // Add the link to DOM
    document.body.appendChild(downloadLink);

    // Click download link
    downloadLink.click();
}

function exportTableToCSV(filename, id) {
    var csv = [];
    var rows = document.getElementById(id).querySelectorAll("table tr");

    for (var i = 0; i < rows.length; i++) {
        var row = [], cols = rows[i].querySelectorAll("td, th");

        for (var j = 0; j < cols.length; j++)
            row.push(cols[j].innerText);

        csv.push(row.join(","));
    }

    // Download CSV file
    downloadCSV2(csv.join("\n"), filename);
}