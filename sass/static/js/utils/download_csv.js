function downloadCSV(url, downloadButton, csv_name=null, email = false) {
    var downloadCSVXhr = $.get({
        url: url,
        dataType: 'json',
        success: function (data) {
            if (email) {
                return
            }
            if (data['status'] !== "success") {
                if (data['status'] === "failed") {
                    if (downloadCSVXhr) {
                        downloadCSVXhr.abort();
                    }
                    downloadButton.html('Download as CSV');
                    downloadButton.prop("disabled", false);
                } else {
                    setTimeout(
                        function () {
                            downloadCSV(url, downloadButton, csv_name, email);
                        }, 5000);
                }
            } else {
                var is_safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
                var filename;
                if(data['filename']){
                    filename = data['filename']
                }else {
                    filename = data['message']
                }
                var a = window.document.createElement('a');
                if (csv_name) {
                    a.download = csv_name + '.csv';
                } else {
                    a.download = filename;
                }
                a.href = '/uploaded/processed_csv/' + filename;
                a.click();

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

