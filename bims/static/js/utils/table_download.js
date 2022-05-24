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

    showDownloadPopup('TABLE', title, function () {
        html2canvas(table, {
            onrendered: function (canvas) {
                let link = document.createElement('a');
                link.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
                link.download = title + '.png';
                link.click();
            }
        })
    })
}

$(function () {
    $('.download-table').click(tablePngDownload);
});