function tablePngDownload(e) {
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

    showDownloadPopup('TABLE', title, function (downloadRequestId) {
        html2canvas(table, {
            onrendered: function (canvas) {
                canvas.toBlob(function (blob) {
                    uploadToDownloadRequest(downloadRequestId, blob, title + '.png');
                }, 'image/png');
            }
        })
    })
}

$(function () {
    $('.download-table').click(tablePngDownload);
});