function downloadCSV(url, downloadButton) {
    var downloadCSVXhr = $.get({
        url: url,
        dataType: 'json',
        success: function (data) {
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
                            downloadCSV(url, downloadButton);
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
                if (is_safari) {
                    var a = window.document.createElement('a');
                    a.href = '/uploaded/csv_processed/' + filename;
                    a.download = filename;
                    a.click();
                } else {
                    location.replace('/uploaded/csv_processed/' + filename);
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

function onDownloadTableClicked(e) {
    let button = $(e.target);
    let maxAttempt = 10;
    let attempt = 1;
    let container = button.parent();
    let found = false;
    let title = button.data('download-title');
    do {
        if (container.hasClass('table-container')) {
            found = true;
        } else {
            container = container.parent();
            attempt++;
        }
    }
    while (!found && attempt < maxAttempt);
    if (!container) {
        return false;
    }
    let table = container.find('.table');
    table[0].scrollIntoView();
    html2canvas(table, {
        onrendered: function (canvas) {
            let link = document.createElement('a');
            link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
            link.download = title + '.png';
            link.click();
        }
    })
}

$(function () {
    $('.download-table').click(onDownloadTableClicked);
});
